"""
Lightweight Local Semantic Vector Store.
Implements TF-IDF normalized cosine similarity retrieval with local JSON disk persistence.
Avoids heavy, platform-incompatible C++ dependencies (e.g. Chroma/Faiss build errors on Windows)
while delivering fast, deterministic semantic retrieval over past research runs.
"""

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

from cognisynth.config import settings
from cognisynth.logging_config import logger


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into words and character sub-tokens."""
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    # Add simple bigrams for phrase awareness
    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    return tokens + bigrams


class LocalVectorStore:
    """Zero-dependency local vector store for semantic retrieval across research sessions."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (settings.data_dir / "vector_store.json")
        self.documents: list[dict[str, Any]] = []
        self.idf: dict[str, float] = {}
        self.load()

    def _compute_tf(self, tokens: list[str]) -> dict[str, float]:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0.0) + 1.0
        # Normalize TF
        total = len(tokens) or 1
        for k in tf:
            tf[k] = tf[k] / total
        return tf

    def _update_idf(self) -> None:
        doc_count = len(self.documents)
        if doc_count == 0:
            self.idf = {}
            return

        df: dict[str, int] = {}
        for doc in self.documents:
            tokens = set(doc.get("tokens", []))
            for tok in tokens:
                df[tok] = df.get(tok, 0) + 1

        self.idf = {tok: math.log((1 + doc_count) / (1 + count)) + 1.0 for tok, count in df.items()}

    def _vectorize(self, text: str) -> dict[str, float]:
        tokens = _tokenize(text)
        tf = self._compute_tf(tokens)
        vec = {}
        norm_sq = 0.0
        for tok, val in tf.items():
            idf_val = self.idf.get(tok, 1.0)
            score = val * idf_val
            vec[tok] = score
            norm_sq += score * score

        norm = math.sqrt(norm_sq) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def add_document(self, text: str, metadata: Optional[dict[str, Any]] = None, doc_id: Optional[str] = None) -> str:
        """Add a text document and update the index."""
        import uuid

        doc_id = doc_id or f"vdoc_{uuid.uuid4().hex[:8]}"
        tokens = _tokenize(text)
        doc_record = {
            "doc_id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "tokens": tokens,
        }
        self.documents.append(doc_record)
        self._update_idf()
        self.persist()
        return doc_id

    def similarity_search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Search for top-k semantically relevant documents using cosine similarity."""
        if not self.documents or not query.strip():
            return []

        query_vec = self._vectorize(query)
        scored: list[tuple[float, dict[str, Any]]] = []

        for doc in self.documents:
            doc_vec = self._vectorize(doc["text"])
            # Cosine similarity between unit vectors is the dot product
            sim = sum(query_vec.get(k, 0.0) * doc_vec.get(k, 0.0) for k in query_vec)
            if sim > 0.01:
                scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, doc in scored[:top_k]:
            results.append({
                "doc_id": doc["doc_id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "similarity_score": round(sim, 4),
            })
        return results

    def persist(self) -> None:
        """Save documents to JSON storage."""
        try:
            os.makedirs(self.storage_path.parent, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to persist vector store: {exc}")

    def load(self) -> None:
        """Load documents from JSON storage if exists."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                self._update_idf()
            except Exception as exc:
                logger.warning(f"Could not load vector store from {self.storage_path}: {exc}")
                self.documents = []


_vector_store_instance: Optional[LocalVectorStore] = None


def get_vector_store() -> LocalVectorStore:
    """Singleton getter for the persistent vector store."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LocalVectorStore()
    return _vector_store_instance
