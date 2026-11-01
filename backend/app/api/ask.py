"""Ask API endpoint for direct Q&A without chat session. """

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.rag.rag_engine import RAGEngine

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None
    top_k: Optional[int] = None


def _generate_suggestions(analysis: dict) -> List[str]:
    # Reuse same suggestion logic as chat endpoint
    company = analysis.get("detected_company")
    topics = analysis.get("detected_topics", [])
    suggestions: List[str] = []
    if company:
        suggestions.append(f"What was the complete selection process at {company}?")
        suggestions.append(f"What interview questions were asked at {company}?")
        suggestions.append(f"What preparation tips are available for {company}?")
    if "CTC" in topics or "Stipend" in topics:
        suggestions.append("Which companies have the highest documented CTC?")
    if not suggestions:
        suggestions = [
            "What was IVP's online assessment pattern?",
            "What questions were asked at Network Marvels?",
            "What does the VESIT policy say about placements?",
        ]
    return suggestions[:3]


@router.post("/ask")
def ask(req: AskRequest):
    """Direct question answering without persisting a chat session.

    Returns the same payload shape as the chat endpoint (answer, sources,
    suggested_questions, and retrieval metadata) so the frontend can reuse
    its existing UI components.
    """
    engine = RAGEngine()
    result = engine.answer(
        query=req.question,
        filter_company=req.filter_company,
        filter_doc_type=req.filter_doc_type,
        top_k=req.top_k,
    )
    if not result:
        raise HTTPException(status_code=500, detail="RAG engine failed to produce a result")

    sources = result.get("sources", [])
    analysis = result.get("analysis", {})
    suggested = _generate_suggestions(analysis)

    return {
        "message": {
            "role": "assistant",
            "content": result.get("answer", ""),
            "sources": sources,
            "suggested_questions": suggested,
            "retrieval_metadata": {
                "evidence_found": result.get("evidence_found", False),
                "total_ms": result.get("total_ms"),
                "retrieval_ms": result.get("retrieval_ms"),
                "generation_ms": result.get("generation_ms"),
                "llm_error": result.get("llm_error"),
                "detected_company": analysis.get("detected_company"),
                "detected_topics": analysis.get("detected_topics", []),
            },
        }
    }

