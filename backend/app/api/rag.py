"""RAG retrieval and explorer endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import httpx

from app.config import settings
from app.database.base import get_db
from app.services.embeddings.embedder import EmbeddingService
from app.services.rag.rag_engine import RAGEngine
from app.services.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter()


class RetrieveRequest(BaseModel):
    query: str
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None
    top_k: Optional[int] = None


class ExploreRequest(BaseModel):
    query: str
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None


@router.post("/rag/retrieve")
def rag_retrieve(req: RetrieveRequest):
    from app.services.rag.query_classifier import classify_query

    analysis = classify_query(req.query)
    if req.filter_company:
        analysis.detected_company = req.filter_company
        analysis.chroma_where = {"company": {"$eq": req.filter_company}}
    if req.filter_doc_type and req.filter_doc_type != "all":
        analysis.doc_category = req.filter_doc_type

    collection = (
        "policy_documents"
        if analysis.doc_category == "policy"
        else "placement_experiences"
    )

    retriever = HybridRetriever()
    chunks = retriever.retrieve(
        query=req.query,
        collection_name=collection,
        n_results=req.top_k or settings.RETRIEVAL_TOP_K,
        where=analysis.chroma_where,
    )

    return [
        {
            "chunk_id": c.get("id", ""),
            "document_id": str(c.get("metadata", {}).get("document_id", "")),
            "filename": c.get("metadata", {}).get("filename", ""),
            "text": c.get("text", ""),
            "score": round(c.get("score", 0), 4),
            "rrf_score": round(c.get("rrf_score", 0), 6),
            "metadata": c.get("metadata", {}),
            "company": c.get("metadata", {}).get("company", ""),
            "page": c.get("metadata", {}).get("page_number"),
        }
        for c in chunks
    ]


@router.post("/rag/explore")
def rag_explore(req: ExploreRequest):
    engine = RAGEngine()
    result = engine.explore(
        query=req.query,
        filter_company=req.filter_company,
        filter_doc_type=req.filter_doc_type,
    )
    return result


@router.get("/rag/status")
def rag_status():
    embedder = EmbeddingService()
    ollama_ok = False
    try:
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    return {
        "ollama_available": ollama_ok,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_store_size": embedder.get_total_vectors(),
        "vector_store_healthy": embedder.is_healthy,
    }

