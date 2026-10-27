"""
Atomic claim and evidence extraction engine.
Parses unstructured source documents into verifiable claims linked to verbatim evidence snippets.
"""

import json
import re
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Source, Document, Claim, Evidence, ClaimType, ClaimStatus
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


CLAIM_EXTRACT_SYSTEM_PROMPT = """You are an expert Fact-Extraction and Evidence Intelligence Agent.
Extract 3 to 6 atomic, verifiable factual claims and concrete evidence quotes from the provided text.

For each claim:
- "text": Exact propositional statement of fact or measurement.
- "type": "factual" or "statistical" or "predictive"
- "snippet": Verbatim supporting snippet from the text (under 250 characters).
- "confidence": Float between 0.0 and 1.0 based on clarity and certainty in text.

Format your output strictly as a valid JSON array:
[
  {
    "text": "Antigravity supports multi-agent graph workflows.",
    "type": "factual",
    "snippet": "Antigravity provides full support for coordinating complex multi-agent graphs...",
    "confidence": 0.95
  }
]
"""


def _heuristic_claim_extraction(source: Source, document: Document) -> tuple[list[Claim], list[Evidence]]:
    """Heuristic fallback extraction for rapid, offline, or test environments."""
    sentences = re.split(r"(?<=[.!?])\s+", document.text)
    claims: list[Claim] = []
    evidences: list[Evidence] = []

    boilerplate_triggers = [
        "copyright", "terms of service", "privacy policy", "about press", "contact us",
        "creator advertise", "all rights reserved", "cookie policy", "how youtube works",
        "test new features", "subscribe", "sign in", "enable javascript", "cookies"
    ]

    candidates = [
        s.strip() for s in sentences
        if len(s.strip()) > 35
        and not any(bp in s.lower() for bp in boilerplate_triggers)
        and (any(c.isdigit() for c in s) or any(kw in s.lower() for kw in ["increase", "result", "demonstrate", "show", "percent", "%", "benchmark", "achieve", "growth", "policy", "summit", "agreement", "member"]))
    ]

    for sent in candidates[:4]:
        ev = Evidence(
            source_id=source.source_id,
            snippet=sent[:250],
            relevance=0.85,
            directness=0.9,
        )
        clm = Claim(
            text=sent,
            type=ClaimType.STATISTICAL if ("%" in sent or any(c.isdigit() for c in sent)) else ClaimType.FACTUAL,
            importance=0.7,
            status=ClaimStatus.UNVERIFIED,
            evidence_refs=[ev.evidence_id],
            confidence=0.75,
        )
        ev.claim_id = clm.claim_id
        evidences.append(ev)
        claims.append(clm)

    return claims, evidences


def extract_claims_and_evidence(
    source: Source,
    document: Document,
    use_llm: bool = True,
) -> tuple[list[Claim], list[Evidence]]:
    """
    Extract atomic propositions and evidence snippets from a document.
    """
    if not document.text or len(document.text.strip()) < 50:
        return [], []

    if not use_llm:
        return _heuristic_claim_extraction(source, document)

    try:
        llm = get_model_router().get_fast_model()
        sample_text = document.text[:4000]
        messages = [
            SystemMessage(content=CLAIM_EXTRACT_SYSTEM_PROMPT),
            HumanMessage(content=f"Source: {source.title} ({source.url})\n\nDocument Text:\n{sample_text}"),
        ]
        response = llm.invoke(messages)
        text = _message_text(response).strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        items = json.loads(text)
        if not isinstance(items, list):
            return _heuristic_claim_extraction(source, document)

        claims: list[Claim] = []
        evidences: list[Evidence] = []

        for item in items[:6]:
            claim_text = str(item.get("text", "")).strip()
            snippet = str(item.get("snippet", claim_text)).strip()
            if not claim_text or any(bp in claim_text.lower() for bp in boilerplate_triggers):
                continue

            raw_type = str(item.get("type", "factual")).lower()
            try:
                ctype = ClaimType(raw_type)
            except ValueError:
                ctype = ClaimType.FACTUAL

            conf = float(item.get("confidence", 0.8))
            conf = min(1.0, max(0.1, conf))

            ev = Evidence(
                source_id=source.source_id,
                snippet=snippet[:300],
                relevance=0.88,
                directness=0.9,
            )
            clm = Claim(
                text=claim_text,
                type=ctype,
                importance=0.8,
                status=ClaimStatus.UNVERIFIED,
                evidence_refs=[ev.evidence_id],
                confidence=conf,
            )
            ev.claim_id = clm.claim_id
            claims.append(clm)
            evidences.append(ev)

        return claims, evidences

    except Exception as exc:
        logger.info(f"LLM claim extraction fallback used ({exc}).")
        return _heuristic_claim_extraction(source, document)
