"""Embedding service using sentence-transformers + ChromaDB."""
from __future__ import annotations

import os
import threading
from typing import Dict, List, Optional

# Enforce offline mode so sentence-transformers reads from local disk cache without network retries
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Singleton-style embedding service. Thread-safe model loading."""

    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmbeddingService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._model = None
        self._chroma_client = None
        self._load()

    def _load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            try:
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
            except Exception:
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded.")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            self._model = None

        try:
            import chromadb  # type: ignore

            self._fix_chroma_config_if_needed()
            logger.info("Connecting to ChromaDB at %s", settings.CHROMA_PATH)
            self._chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
            logger.info("ChromaDB connected.")
        except Exception as exc:
            logger.error("Failed to connect to ChromaDB: %s", exc)
            self._chroma_client = None

    def _fix_chroma_config_if_needed(self) -> None:
        """Repairs any corrupted empty config_json_str in ChromaDB sqlite metadata."""
        try:
            import sqlite3
            from pathlib import Path

            db_path = Path(settings.CHROMA_PATH) / "chroma.sqlite3"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                default_config = '{"hnsw_configuration": {"space": "cosine", "ef_construction": 100, "ef_search": 10, "num_threads": 10, "M": 16, "resize_factor": 1.2, "batch_size": 100, "sync_threshold": 1000, "_type": "HNSWConfigurationInternal"}, "_type": "CollectionConfigurationInternal"}'
                cursor.execute(
                    "UPDATE collections SET config_json_str = ? WHERE config_json_str IS NULL OR config_json_str = '' OR config_json_str = '{}';",
                    (default_config,),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning("Auto-repair of ChromaDB config skipped: %s", e)

    # â”€â”€ Public API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection with cosine distance."""
        if self._chroma_client is None:
            raise RuntimeError("ChromaDB client not initialised")
        try:
            return self._chroma_client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            if "_type" in str(exc) or isinstance(exc, KeyError):
                self._fix_chroma_config_if_needed()
                return self._chroma_client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
            raise

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of texts."""
        if self._model is None:
            raise RuntimeError("Embedding model not loaded")
        embeddings = self._model.encode(texts, show_progress_bar=False, batch_size=32)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed([text])[0]

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        metadatas: List[Dict],
        ids: List[str],
    ) -> List[str]:
        """Embed and upsert chunks into ChromaDB. Returns the list of ids."""
        if not chunks:
            return []
        collection = self.get_or_create_collection(collection_name)
        embeddings = self.embed(chunks)

        # Sanitise metadata: ChromaDB only accepts str/int/float/bool
        clean_metas = []
        for meta in metadatas:
            clean = {}
            for k, v in meta.items():
                if v is None:
                    clean[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            clean_metas.append(clean)

        collection.upsert(
            documents=chunks,
            embeddings=embeddings,
            metadatas=clean_metas,
            ids=ids,
        )
        return ids

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 8,
        where: Optional[Dict] = None,
    ) -> Dict:
        """Semantic search in a collection."""
        collection = self.get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        n = min(n_results, count)
        query_embedding = self.embed([query_text])[0]
        kwargs: Dict = {"query_embeddings": [query_embedding], "n_results": n, "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where
        return collection.query(**kwargs)

    def delete_by_document_id(self, collection_name: str, document_id: int) -> None:
        """Remove all vectors belonging to a document."""
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.get(where={"document_id": document_id})
            if results and results.get("ids"):
                collection.delete(ids=results["ids"])
                logger.info("Deleted %d vectors for document_id=%d", len(results["ids"]), document_id)
        except Exception as exc:
            logger.warning("Could not delete vectors for document_id=%d: %s", document_id, exc)

    def get_total_vectors(self) -> int:
        """Return total vector count across all collections."""
        if self._chroma_client is None:
            return 0
        try:
            total = 0
            for col in self._chroma_client.list_collections():
                total += col.count()
            return total
        except Exception:
            return 0

    @property
    def is_healthy(self) -> bool:
        return self._model is not None and self._chroma_client is not None
