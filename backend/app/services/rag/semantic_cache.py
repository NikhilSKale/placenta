"""Semantic Cache: Caches query-answer pairs using dense vector similarity.

If a new question is semantically similar to an existing cached question
(cosine similarity >= threshold), return the cached answer immediately,
saving LLM inference time and token compute.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.logging import get_logger
from app.services.embeddings.embedder import EmbeddingService

logger = get_logger(__name__)


class CachedEntry:
    def __init__(
        self,
        query: str,
        embedding: List[float],
        result: Dict[str, Any],
        filter_company: Optional[str] = None,
        filter_doc_type: Optional[str] = None,
        created_at: float = None,
    ):
        self.query = query
        self.embedding = np.array(embedding, dtype=np.float32)
        # Normalize for cosine similarity
        norm = np.linalg.norm(self.embedding)
        if norm > 0:
            self.embedding /= norm
        self.result = result
        self.filter_company = filter_company
        self.filter_doc_type = filter_doc_type
        self.created_at = created_at or time.time()
        self.hits = 0


class SemanticCache:
    """In-memory semantic cache with cosine similarity matching and TTL support."""

    def __init__(self, similarity_threshold: float = 0.92, max_entries: int = 500, ttl_seconds: float = 86400):
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.cache: List[CachedEntry] = []
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = EmbeddingService()
        return self._embedder

    def lookup(
        self,
        query: str,
        filter_company: Optional[str] = None,
        filter_doc_type: Optional[str] = None,
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Looks up query in semantic cache.
        Returns: (result_dict, similarity_score) if hit, else None
        """
        if not self.cache:
            return None

        now = time.time()
        # Clean expired entries
        self.cache = [e for e in self.cache if (now - e.created_at) < self.ttl_seconds]

        try:
            query_emb = np.array(self.embedder.embed_query(query), dtype=np.float32)
            norm = np.linalg.norm(query_emb)
            if norm > 0:
                query_emb /= norm
        except Exception as exc:
            logger.warning("Failed to generate embedding for cache lookup: %s", exc)
            return None

        best_entry: Optional[CachedEntry] = None
        best_score: float = -1.0

        for entry in self.cache:
            # Must match filters if specified
            if entry.filter_company != filter_company or entry.filter_doc_type != filter_doc_type:
                continue

            similarity = float(np.dot(query_emb, entry.embedding))
            if similarity > best_score:
                best_score = similarity
                best_entry = entry

        if best_entry and best_score >= self.similarity_threshold:
            best_entry.hits += 1
            logger.info("Semantic cache HIT (score=%.4f) for query: '%s' ~ '%s'", best_score, query, best_entry.query)
            # Copy result and mark cached flag
            res = dict(best_entry.result)
            res["cached"] = True
            res["cache_similarity"] = round(best_score, 4)
            res["original_cached_query"] = best_entry.query
            return res, best_score

        return None

    def store(
        self,
        query: str,
        result: Dict[str, Any],
        filter_company: Optional[str] = None,
        filter_doc_type: Optional[str] = None,
    ) -> None:
        """Stores a successful RAG result in the semantic cache."""
        # Only cache results where evidence was found and no LLM errors occurred
        if not result.get("evidence_found") or result.get("llm_error"):
            return

        if len(self.cache) >= self.max_entries:
            # Evict least frequently used / oldest
            self.cache.sort(key=lambda e: (e.hits, e.created_at))
            self.cache.pop(0)

        try:
            emb = self.embedder.embed_query(query)
            entry = CachedEntry(
                query=query,
                embedding=emb,
                result=result,
                filter_company=filter_company,
                filter_doc_type=filter_doc_type,
            )
            self.cache.append(entry)
            logger.info("Stored query in semantic cache (total entries: %d): '%s'", len(self.cache), query)
        except Exception as exc:
            logger.warning("Could not store in semantic cache: %s", exc)

    def clear(self) -> None:
        self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        return {
            "total_cached_queries": len(self.cache),
            "total_cache_hits": sum(e.hits for e in self.cache),
            "similarity_threshold": self.similarity_threshold,
        }


semantic_cache = SemanticCache()
