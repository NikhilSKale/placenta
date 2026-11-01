"""Document management API endpoints."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import IngestionError
from app.core.logging import get_logger
from app.database.base import get_db
from app.models.models import Document, DocumentChunk, ExtractedFact
from app.services.embeddings.embedder import EmbeddingService
from app.services.ingestion.file_validator import sanitize_filename, validate_file_extension
from app.services.ingestion.pipeline import IngestionPipeline

logger = get_logger(__name__)
router = APIRouter()


def _doc_to_dict(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "company_name": doc.company_name,
        "company": doc.company_name,  # alias for frontend compatibility
        "student_name": doc.student_name,
        "year": doc.year,
        "num_pages": doc.num_pages,
        "pages": doc.num_pages,
        "num_chunks": doc.num_chunks,
        "chunk_count": doc.num_chunks,
        "extraction_status": doc.extraction_status,
        "ingestion_status": doc.ingestion_status,
        "status": doc.ingestion_status,
        "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [_doc_to_dict(d) for d in docs]


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("placement_experience"),
    db: Session = Depends(get_db),
):
    # Validate
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_name = sanitize_filename(file.filename)
    try:
        validate_file_extension(safe_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Size check
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum is {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save to uploads directory
    upload_dir = Path(settings.UPLOADS_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / safe_name
    # Avoid overwriting: add suffix if exists
    counter = 1
    while dest.exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        dest = upload_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(contents)

    # Ingest
    pipeline = IngestionPipeline(db=db)
    try:
        doc = pipeline.ingest_file(str(dest), doc_type=doc_type)
    except IngestionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return _doc_to_dict(doc)


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    result = _doc_to_dict(doc)
    result["raw_text"] = doc.raw_text
    return result


@router.get("/documents/{doc_id}/facts")
def get_document_facts(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    facts = db.query(ExtractedFact).filter(ExtractedFact.document_id == doc_id).all()
    return [
        {
            "id": str(f.id),
            "field": f.field_name,
            "value": f.field_value,
            "evidence": f.evidence_text,
            "source_page": f.source_page,
            "extraction_method": f.extraction_method,
            "is_manually_corrected": f.is_manually_corrected,
            "evidence_status": f.evidence_status,
        }
        for f in facts
    ]


@router.get("/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    return [
        {
            "id": str(c.id),
            "document_id": str(c.document_id),
            "chunk_index": c.chunk_index,
            "text": c.text,
            "metadata": json.loads(c.chunk_metadata_json or "{}"),
            "embedding_id": c.embedding_id,
        }
        for c in chunks
    ]


@router.post("/documents/{doc_id}/reindex")
def reindex_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove existing vectors
    embedder = EmbeddingService()
    collection = (
        "policy_documents" if doc.doc_type == "policy" else "placement_experiences"
    )
    embedder.delete_by_document_id(collection, doc.id)

    # Reset status and reprocess
    doc.ingestion_status = "pending"
    doc.file_hash = None  # force re-hash
    db.commit()

    pipeline = IngestionPipeline(db=db)
    try:
        doc = pipeline.ingest_file(doc.file_path, doc_type=doc.doc_type)
    except IngestionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "document": _doc_to_dict(doc)}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove vectors from ChromaDB
    embedder = EmbeddingService()
    collection = (
        "policy_documents" if doc.doc_type == "policy" else "placement_experiences"
    )
    embedder.delete_by_document_id(collection, doc.id)

    # Delete from DB (cascades to chunks, facts, etc.)
    db.delete(doc)
    db.commit()
    return {"success": True}

