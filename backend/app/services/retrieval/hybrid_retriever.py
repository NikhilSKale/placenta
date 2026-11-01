"""Hybrid retrieval: dense (ChromaDB) + BM25 sparse, merged with Reciprocal Rank Fusion."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from app.config import settings
from app.core.logging import get_logger
from app.services.retrieval.vector_store import VectorStore

logger = get_logger(__name__)


def _reciprocal_rank_fusion(
    ranked_lists: List[List[Dict]], k: int = 60
) -> List[Dict]:
    """Merge multiple ranked lists using RRF. Each item must have an 'id' key."""
    scores: Dict[str, float] = {}
    items: Dict[str, Dict] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            iid = item["id"]
            scores[iid] = scores.get(iid, 0.0) + 1.0 / (k + rank)
            if iid not in items:
                items[iid] = item

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    result = []
    for iid in sorted_ids:
        entry = dict(items[iid])
        entry["rrf_score"] = scores[iid]
        result.append(entry)
    return result


class HybridRetriever:
    """Combines dense semantic search and BM25 sparse search."""

    def __init__(self):
        self.vector_store = VectorStore()
        self._bm25_index: Optional[object] = None
        self._bm25_corpus: List[Dict] = []

    def retrieve(
        self,
        query: str,
        collection_name: str = "placement_experiences",
        n_results: int = None,
        where: Optional[Dict] = None,
        use_bm25: bool = True,
    ) -> List[Dict]:
        """Retrieve and merge results from dense + BM25 retrieval."""
        n = n_results or settings.RETRIEVAL_TOP_K

        # 1. Dense retrieval
        dense_results = self.vector_store.search(
            collection_name=collection_name,
            query=query,
            n_results=n * 2,
            where=where,
        )

        if not use_bm25 or not dense_results:
            # Return dense only, filtered by threshold
            filtered = [
                r for r in dense_results
                if r.get("score", 0) >= settings.SIMILARITY_THRESHOLD
            ]
            return filtered[:n]

        # 2. BM25 retrieval
        bm25_results = self._bm25_search(query, dense_results, n * 2)

        # 3. Merge with RRF
        merged = _reciprocal_rank_fusion([dense_results, bm25_results])

        # 4. Threshold filter and limit
        filtered = [
            r for r in merged
            if r.get("score", 0) >= settings.SIMILARITY_THRESHOLD
            or r.get("rrf_score", 0) > 0
        ]
        return filtered[:n]

    def _bm25_search(
        self, query: str, candidate_pool: List[Dict], n: int
    ) -> List[Dict]:
        """Run BM25 over the candidate pool texts."""
        if not candidate_pool:
            return []
        try:
            from rank_bm25 import BM25Okapi  # type: ignore

            corpus = [item["text"].lower().split() for item in candidate_pool]
            bm25 = BM25Okapi(corpus)
            query_tokens = query.lower().split()
            scores = bm25.get_scores(query_tokens)
            ranked = sorted(
                zip(candidate_pool, scores),
                key=lambda x: x[1],
                reverse=True,
            )
            results = []
            for item, score in ranked[:n]:
                entry = dict(item)
                entry["bm25_score"] = float(score)
                results.append(entry)
            return results
        except Exception as exc:
            logger.warning("BM25 failed: %s — returning empty BM25 results", exc)
            return []

