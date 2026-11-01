"""Chat API endpoints."""
from __future__ import annotations

import datetime
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.base import get_db
from app.models.models import ChatMessage, ChatSession
from app.services.rag.rag_engine import RAGEngine

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None
    top_k: Optional[int] = None


def _get_or_create_session(db: Session, session_id: Optional[int], first_message: str) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            return session
    title = first_message[:60] + ("..." if len(first_message) > 60 else "")
    session = ChatSession(title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    session = _get_or_create_session(db, req.session_id, req.message)

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=req.message,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(user_msg)
    db.commit()

    # Run RAG
    engine = RAGEngine()
    result = engine.answer(
        query=req.message,
        filter_company=req.filter_company,
        filter_doc_type=req.filter_doc_type,
        top_k=req.top_k,
    )

    sources = result.get("sources", [])
    # Generate follow-up suggestions based on topic detection
    analysis = result.get("analysis", {})
    suggested = _generate_suggestions(analysis)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        created_at=datetime.datetime.utcnow(),
        sources_json=json.dumps(sources),
        retrieval_metadata_json=json.dumps({
            "evidence_found": result.get("evidence_found", False),
            "total_ms": result.get("total_ms"),
            "retrieval_ms": result.get("retrieval_ms"),
            "generation_ms": result.get("generation_ms"),
            "detected_company": analysis.get("detected_company"),
            "detected_topics": analysis.get("detected_topics", []),
            "llm_error": result.get("llm_error"),
        }),
    )
    db.add(assistant_msg)

    # Update session timestamp
    session.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(assistant_msg)

    return {
        "message": {
            "id": str(assistant_msg.id),
            "role": "assistant",
            "content": assistant_msg.content,
            "sources": sources,
            "suggested_questions": suggested,
            "created_at": assistant_msg.created_at.isoformat(),
            "retrieval_metadata": json.loads(assistant_msg.retrieval_metadata_json or "{}"),
        },
        "session_id": session.id,
        "session_title": session.title,
    }


def _generate_suggestions(analysis: dict) -> list[str]:
    company = analysis.get("detected_company")
    topics = analysis.get("detected_topics", [])
    suggestions = []
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


@router.get("/chats")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50).all()
    result = []
    for s in sessions:
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        last_msg = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == s.id, ChatMessage.role == "assistant")
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        result.append({
            "id": str(s.id),
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "message_count": msg_count,
            "last_message": last_msg.content[:100] if last_msg else None,
        })
    return result


@router.get("/chats/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return {
        "session": {
            "id": str(session.id),
            "title": session.title,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        },
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources_json or "[]"),
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "retrieval_metadata": json.loads(m.retrieval_metadata_json or "{}"),
            }
            for m in messages
        ],
    }


@router.delete("/chats/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"success": True}

