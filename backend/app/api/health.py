"""Health check endpoint."""
from __future__ import annotations

import httpx
from fastapi import APIRouter

from app.config import settings
from app.core.logging import get_logger
from app.services.embeddings.embedder import EmbeddingService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    embedder = EmbeddingService()
    ollama_ok = False
    ollama_model = settings.OLLAMA_MODEL
    try:
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=1.0)
        ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    return {
        "status": "ok",
        "ollama_available": ollama_ok,
        "ollama_model": ollama_model,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_store_healthy": embedder.is_healthy,
        "vector_store_size": embedder.get_total_vectors(),
    }
