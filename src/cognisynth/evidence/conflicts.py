"""
Contradiction and Conflict Detection Engine.
Identifies opposing statements, discrepancies, and conflicting claims across sources.
"""

import re
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Claim, Evidence, Source
from cognisynth.schemas.report import Conflict, ConflictSeverity
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


OPPOSING_TERMS = [
    ("increase", "decrease"),
    ("rise", "fall"),
    ("higher", "lower"),
    ("growth", "decline"),
    ("supported", "unsupported"),
    ("effective", "ineffective"),
    ("safe", "dangerous"),
    ("secure", "vulnerable"),
    ("outperforms", "underperforms"),
    ("surpassed", "lagged"),
]


def detect_heuristic_contradictions(claims: list[Claim]) -> list[Conflict]:
    """
    Detect obvious opposing polarity and numerical discrepancies between pairs of claims.
    """
    conflicts: list[Conflict] = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            c1 = claims[i]
            c2 = claims[j]

            t1 = c1.text.lower()
            t2 = c2.text.lower()

            # Polarity check
            for pos, neg in OPPOSING_TERMS:
                if (pos in t1 and neg in t2) or (neg in t1 and pos in t2):
                    conflicts.append(
                        Conflict(
                            claim_refs=[c1.claim_id, c2.claim_id],
                            explanation=f"Contradictory polarity detected regarding '{pos}/{neg}': '{c1.text}' vs '{c2.text}'",
                            severity=ConflictSeverity.MEDIUM,
                            resolution="Cross-reference with primary benchmark data to resolve methodology differences.",
                        )
                    )
                    break

            # Numerical discrepancies on similar topics
            nums1 = re.findall(r"\b\d+(?:\.\d+)?%?", t1)
            nums2 = re.findall(r"\b\d+(?:\.\d+)?%?", t2)
            if nums1 and nums2 and nums1 != nums2:
                # Check lexical overlap of remaining words
                words1 = set(re.findall(r"\b[a-z]{4,}\b", t1))
                words2 = set(re.findall(r"\b[a-z]{4,}\b", t2))
                overlap = words1.intersection(words2)
                if len(overlap) >= 3:
                    conflicts.append(
                        Conflict(
                            claim_refs=[c1.claim_id, c2.claim_id],
                            explanation=f"Numerical discrepancy on common subject ({', '.join(list(overlap)[:3])}): '{c1.text}' ({nums1[0]}) vs '{c2.text}' ({nums2[0]})",
                            severity=ConflictSeverity.HIGH,
                            resolution="Reconcile reporting period and sample sizing differences between sources.",
                        )
                    )

    return conflicts


def detect_contradictions_llm(claims: list[Claim], sources_map: dict[str, Source]) -> list[Conflict]:
    """
    Use LLM reasoning to detect nuanced contextual or factual contradictions across claims.
    """
    if len(claims) < 2:
        return []

    claims_summary = "\n".join(
        [f"[{idx}] ID: {c.claim_id} | Text: {c.text}" for idx, c in enumerate(claims[:10], start=1)]
    )

    prompt = f"""Compare these research claims and identify any real contradictions, opposing findings, or conflicting numbers:

{claims_summary}

If no strong contradictions exist, return empty array [].
If contradictions exist, return JSON array:
[
  {{
    "claim_refs": ["claim_id_1", "claim_id_2"],
    "explanation": "Clear explanation of the factual dispute",
    "severity": "medium",
    "resolution": "How to reconcile or what causes the discrepancy"
  }}
]
"""
    try:
        llm = get_model_router().get_reasoning_model()
        messages = [
            SystemMessage(content="You are an expert Contradiction and Verification Analyst. Return strict JSON array."),
            HumanMessage(content=prompt),
        ]
        resp = llm.invoke(messages)
        text = _message_text(resp).strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        import json
        data = json.loads(text)
        conflicts = []
        for item in data:
            refs = item.get("claim_refs", [])
            explanation = item.get("explanation", "")
            if refs and explanation:
                sev_str = str(item.get("severity", "medium")).lower()
                try:
                    sev = ConflictSeverity(sev_str)
                except ValueError:
                    sev = ConflictSeverity.MEDIUM
                conflicts.append(
                    Conflict(
                        claim_refs=refs,
                        explanation=explanation,
                        severity=sev,
                        resolution=item.get("resolution", "Independent verification required."),
                    )
                )
        return conflicts if conflicts else detect_heuristic_contradictions(claims)

    except Exception as exc:
        logger.info(f"Contradiction LLM check skipped ({exc}); using heuristic detector.")
        return detect_heuristic_contradictions(claims)
