"""Structure-aware text chunker for placement experience and policy documents."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from app.config import settings
from app.core.logging import get_logger
from app.services.ingestion.pdf_parser import ParsedDocument

logger = get_logger(__name__)

# Heading patterns
HEADING_PATTERNS = [
    re.compile(r"^(Round\s*\d+[:\-–]?.*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(Online\s+Test|Technical\s+Interview|HR\s+Interview|Group\s+Discussion|Aptitude[:\-–].*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(Preparation|Tips|Resources|Experience|Introduction|Background|About[:\-–].*)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(\d+[\.\)]\s+\w.{5,80})$", re.MULTILINE),
    re.compile(r"^([A-Z][A-Z\s]{4,50}):?\s*$", re.MULTILINE),
]

# Q&A patterns
QA_PATTERN = re.compile(
    r"((?:Q[\.:\)]|Question\s*\d*[\.:\)])\s*.+?)(?=Q[\.:\)]|Question\s*\d*[\.:\)]|$)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


class DocumentChunker:
    """Structure-aware chunker producing semantic chunks from parsed documents."""

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def chunk(
        self,
        parsed_doc: ParsedDocument,
        doc_type: str = "placement_experience",
        document_id: Optional[int] = None,
        company_name: Optional[str] = None,
        student_name: Optional[str] = None,
    ) -> List[Chunk]:
        chunks: List[Chunk] = []
        base_meta = {
            "document_id": document_id,
            "filename": parsed_doc.filename,
            "doc_type": doc_type,
            "company": company_name,
            "student_name": student_name,
        }

        # Process page by page to preserve page_number metadata
        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue
            page_meta = {**base_meta, "page_number": page.page_number}
            page_chunks = self._chunk_page(page_text, page_meta)
            chunks.extend(page_chunks)

        # Assign sequential indices
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.metadata["chunk_id"] = f"{document_id or 'doc'}_chunk_{i}"

        logger.info("Produced %d chunks from %s", len(chunks), parsed_doc.filename)
        return chunks

    def _chunk_page(self, text: str, base_meta: Dict) -> List[Chunk]:
        """Split a single page into chunks using structure-aware logic."""
        chunks: List[Chunk] = []

        # 1. Try Q&A extraction first
        qa_chunks = self._extract_qa_pairs(text, base_meta)
        if qa_chunks:
            remaining = text
            for qa in qa_chunks:
                remaining = remaining.replace(qa.text, "", 1)
            chunks.extend(qa_chunks)
            text = remaining.strip()

        if not text:
            return chunks

        # 2. Detect section boundaries via headings
        sections = self._split_by_headings(text)
        for section_heading, section_text in sections:
            meta = {**base_meta}
            if section_heading:
                meta["section"] = section_heading

            sub_chunks = self._split_text(section_text, meta)
            chunks.extend(sub_chunks)

        return chunks

    def _extract_qa_pairs(self, text: str, base_meta: Dict) -> List[Chunk]:
        """Find Q&A blocks and keep them together as chunks."""
        chunks = []
        for match in QA_PATTERN.finditer(text):
            qa_text = match.group(0).strip()
            if len(qa_text) < 20:
                continue
            meta = {**base_meta, "chunk_type": "qa_pair"}
            chunks.append(Chunk(text=qa_text, metadata=meta))
        return chunks

    def _split_by_headings(self, text: str) -> List[tuple]:
        """Split text into (heading, body) tuples at heading boundaries."""
        sections = []
        current_heading = None
        current_body: List[str] = []

        for line in text.split("\n"):
            is_heading = any(p.match(line.strip()) for p in HEADING_PATTERNS)
            if is_heading and line.strip():
                if current_body:
                    sections.append((current_heading, "\n".join(current_body)))
                current_heading = line.strip()
                current_body = []
            else:
                current_body.append(line)

        if current_body:
            sections.append((current_heading, "\n".join(current_body)))

        if not sections:
            sections = [(None, text)]

        return sections

    def _split_text(self, text: str, meta: Dict) -> List[Chunk]:
        """Split text into chunks respecting size limits with overlap."""
        text = text.strip()
        if not text:
            return []

        # Use LangChain's RecursiveCharacterTextSplitter
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            texts = splitter.split_text(text)
            return [Chunk(text=t, metadata=dict(meta)) for t in texts if t.strip()]
        except Exception as exc:
            logger.warning("RecursiveCharacterTextSplitter failed: %s — using simple split", exc)
            return self._simple_split(text, meta)

    def _simple_split(self, text: str, meta: Dict) -> List[Chunk]:
        """Naive fixed-size split as ultimate fallback."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(text=chunk_text, metadata=dict(meta)))
            start += self.chunk_size - self.chunk_overlap
        return chunks
