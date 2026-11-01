"""Policy API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.models import Document, PolicyClause

router = APIRouter()


@router.get("/policy/sections")
def get_policy_sections(db: Session = Depends(get_db)):
    clauses = (
        db.query(PolicyClause)
        .order_by(PolicyClause.page_number.asc())
        .all()
    )

    if not clauses:
        # Try to get raw text from policy documents
        policy_docs = db.query(Document).filter(Document.doc_type == "policy").all()
        if not policy_docs:
            return {"sections": [], "warning": "No policy documents have been indexed."}
        sections = []
        for doc in policy_docs:
            if doc.raw_text:
                # Split by pages
                for i, page_text in enumerate(doc.raw_text.split("[Page "), 1):
                    if not page_text.strip():
                        continue
                    lines = page_text.strip().split("\n")
                    heading = lines[0][:100] if lines else f"Page {i}"
                    content = "\n".join(lines[1:]).strip()
                    sections.append({
                        "id": f"doc{doc.id}_page{i}",
                        "heading": heading,
                        "content": content,
                        "document_id": str(doc.id),
                        "filename": doc.filename,
                        "page": i,
                    })
        return {"sections": sections}

    return {
        "sections": [
            {
                "id": str(c.id),
                "heading": c.heading or f"Section {c.clause_number}",
                "content": c.content,
                "document_id": str(c.document_id),
                "page": c.page_number,
                "clause_number": c.clause_number,
            }
            for c in clauses
        ]
    }

