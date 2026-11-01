"""Ingestion pipeline: parse → extract → chunk → embed → persist."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import IngestionError
from app.core.logging import get_logger
from app.models.models import Document, DocumentChunk, IngestionJob
from app.services.embeddings.embedder import EmbeddingService
from app.services.extraction.extractor import StructuredExtractor
from app.services.ingestion.chunker import DocumentChunker
from app.services.ingestion.file_validator import compute_file_hash, validate_file_extension
from app.services.ingestion.pdf_parser import PDFParser

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates the full document ingestion flow."""

    def __init__(self, db: Session):
        self.db = db
        self.parser = PDFParser()
        self.chunker = DocumentChunker()
        self.extractor = StructuredExtractor()
        self.embedder = EmbeddingService()

    # ── Public entry points ───────────────────────────────────────────────────

    def ingest_file(self, file_path: str, doc_type: str = "placement_experience") -> Document:
        """Ingest a single file into the system. Skips if already indexed."""
        path = Path(file_path)
        validate_file_extension(path.name)
        file_hash = compute_file_hash(file_path)

        # Idempotency check
        existing = self.db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing and existing.ingestion_status == "completed":
            logger.info("Skipping already-indexed file: %s (hash=%s)", path.name, file_hash[:8])
            return existing

        document = existing or self._create_document_record(file_path, file_hash, doc_type)
        job = IngestionJob(document_id=document.id, status="running", started_at=datetime.datetime.utcnow())
        self.db.add(job)
        self.db.commit()

        try:
            self._run_pipeline(document, job)
        except Exception as exc:
            logger.error("Ingestion failed for %s: %s", path.name, exc, exc_info=True)
            document.ingestion_status = "failed"
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.datetime.utcnow()
            self.db.commit()
            raise IngestionError(f"Failed to ingest {path.name}: {exc}") from exc

        return document

    def scan_and_ingest_directory(self, directory: str, doc_type: str) -> List[Document]:
        """Scan a directory and ingest all supported files."""
        documents = []
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning("Directory does not exist: %s", directory)
            return documents

        for file_path in dir_path.iterdir():
            if file_path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
                continue
            try:
                doc = self.ingest_file(str(file_path), doc_type=doc_type)
                documents.append(doc)
            except Exception as exc:
                logger.error("Failed to ingest %s: %s", file_path.name, exc)
        return documents

    # ── Internal pipeline steps ────────────────────────────────────────────────

    def _create_document_record(self, file_path: str, file_hash: str, doc_type: str) -> Document:
        path = Path(file_path)
        company_name, student_name = self.extractor.extract_names_from_filename(path.name)
        document = Document(
            filename=path.name,
            file_path=file_path,
            file_hash=file_hash,
            doc_type=doc_type,
            company_name=company_name,
            student_name=student_name,
            ingestion_status="pending",
            extraction_status="pending",
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def _run_pipeline(self, document: Document, job: IngestionJob) -> None:
        path = document.file_path
        logger.info("Parsing %s", document.filename)

        # Step 1: Parse
        parsed = self.parser.parse(path)
        document.num_pages = parsed.total_pages
        document.raw_text = parsed.full_text[:50000]  # cap raw text storage
        if parsed.warnings:
            job.warnings_json = json.dumps(parsed.warnings)

        # Step 2: Structured extraction
        logger.info("Extracting structured data from %s", document.filename)
        try:
            self.extractor.extract_and_persist(parsed, document, self.db)
            document.extraction_status = "completed"
        except Exception as exc:
            logger.warning("Extraction partial failure for %s: %s", document.filename, exc)
            document.extraction_status = "partial"

        # Step 3: Chunk
        logger.info("Chunking %s", document.filename)
        chunks = self.chunker.chunk(
            parsed,
            doc_type=document.doc_type,
            document_id=document.id,
            company_name=document.company_name,
            student_name=document.student_name,
        )

        # Step 4: Persist chunks to DB
        self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        chunk_records = []
        for chunk in chunks:
            record = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                chunk_metadata_json=json.dumps(chunk.metadata),
            )
            chunk_records.append(record)
        self.db.add_all(chunk_records)
        self.db.commit()

        # Step 5: Embed and index in ChromaDB
        logger.info("Embedding %d chunks for %s", len(chunks), document.filename)
        collection_name = (
            "placement_experiences" if document.doc_type == "placement_experience" else "policy_documents"
        )
        embedding_ids = self.embedder.upsert_chunks(
            collection_name=collection_name,
            chunks=[c.text for c in chunks],
            metadatas=[c.metadata for c in chunks],
            ids=[f"{document.id}_chunk_{c.chunk_index}" for c in chunks],
        )

        # Update embedding_id on each DB chunk
        for record, emb_id in zip(chunk_records, embedding_ids):
            record.embedding_id = emb_id
        self.db.commit()

        # Finalise
        document.num_chunks = len(chunks)
        document.ingestion_status = "completed"
        document.indexed_at = datetime.datetime.utcnow()
        job.status = "completed"
        job.completed_at = datetime.datetime.utcnow()
        self.db.commit()
        logger.info("Ingestion complete: %s (%d chunks)", document.filename, len(chunks))
