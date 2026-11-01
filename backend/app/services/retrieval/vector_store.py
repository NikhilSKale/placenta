"""ChromaDB vector store wrapper."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.services.embeddings.embedder import EmbeddingService


class VectorStore:
    """Thin wrapper around EmbeddingService for vector store operations."""

    def __init__(self):
        self.embedder = EmbeddingService()

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 8,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """Search and return list of {id, text, metadata, distance}."""
        try:
            results = self.embedder.query(
                collection_name=collection_name,
                query_text=query,
                n_results=n_results,
                where=where,
            )
        except Exception:
            return []

        hits = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            hits.append(
                {
                    "id": chunk_id,
                    "text": doc,
                    "metadata": meta or {},
                    "distance": dist,
                    "score": max(0.0, 1.0 - dist),  # cosine → similarity
                }
            )
        return hits
