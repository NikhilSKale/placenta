"""PDF text extraction using pdfplumber (primary) with PyMuPDF fallback."""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    tables: List[List[List[Optional[str]]]] = field(default_factory=list)
    has_content: bool = True


@dataclass
class ParsedDocument:
    file_path: str
    filename: str
    total_pages: int
    pages: List[PageContent] = field(default_factory=list)
    full_text: str = ""
    parse_method: str = "unknown"
    warnings: List[str] = field(default_factory=list)

    def get_full_text(self) -> str:
        if self.full_text:
            return self.full_text
        return "\n\n".join(
            f"[Page {p.page_number}]\n{p.text}" for p in self.pages if p.text.strip()
        )


class PDFParser:
    """Parses PDF files to structured text with page-level granularity."""

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            doc = self._parse_with_pdfplumber(file_path)
            if not doc or not doc.full_text.strip():
                logger.warning("pdfplumber produced empty text for %s, trying PyMuPDF", file_path)
                doc = self._parse_with_pymupdf(file_path)
            return doc
        elif suffix in {".docx", ".doc"}:
            return self._parse_docx(file_path)
        elif suffix in {".txt", ".md"}:
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    # ── pdfplumber ────────────────────────────────────────────────────────────

    def _parse_with_pdfplumber(self, file_path: str) -> ParsedDocument:
        try:
            import pdfplumber  # type: ignore

            pages: List[PageContent] = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    # Append table text to page text so it's searchable
                    table_texts = []
                    for table in tables:
                        for row in table:
                            row_text = " | ".join(cell or "" for cell in row)
                            if row_text.strip():
                                table_texts.append(row_text)
                    if table_texts:
                        text += "\n" + "\n".join(table_texts)
                    pages.append(PageContent(page_number=i, text=text, tables=tables))

            full_text = "\n\n".join(
                f"[Page {p.page_number}]\n{p.text}" for p in pages if p.text.strip()
            )
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=len(pages),
                pages=pages,
                full_text=full_text,
                parse_method="pdfplumber",
            )
        except Exception as exc:
            logger.error("pdfplumber failed on %s: %s", file_path, exc)
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=0,
                parse_method="pdfplumber_failed",
                warnings=[str(exc)],
            )

    # ── PyMuPDF ────────────────────────────────────────────────────────────────

    def _parse_with_pymupdf(self, file_path: str) -> ParsedDocument:
        try:
            import fitz  # type: ignore  # PyMuPDF

            doc = fitz.open(file_path)
            pages: List[PageContent] = []
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                pages.append(PageContent(page_number=i, text=text))
            doc.close()

            full_text = "\n\n".join(
                f"[Page {p.page_number}]\n{p.text}" for p in pages if p.text.strip()
            )
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=len(pages),
                pages=pages,
                full_text=full_text,
                parse_method="pymupdf",
            )
        except Exception as exc:
            logger.error("PyMuPDF failed on %s: %s", file_path, exc)
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=0,
                parse_method="pymupdf_failed",
                warnings=[str(exc)],
            )

    # ── DOCX ──────────────────────────────────────────────────────────────────

    def _parse_docx(self, file_path: str) -> ParsedDocument:
        try:
            from docx import Document  # type: ignore

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)
            page = PageContent(page_number=1, text=full_text)
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=1,
                pages=[page],
                full_text=full_text,
                parse_method="python-docx",
            )
        except Exception as exc:
            logger.error("python-docx failed on %s: %s", file_path, exc)
            return ParsedDocument(
                file_path=file_path,
                filename=Path(file_path).name,
                total_pages=0,
                parse_method="docx_failed",
                warnings=[str(exc)],
            )

    # ── Plain text ────────────────────────────────────────────────────────────

    def _parse_text(self, file_path: str) -> ParsedDocument:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
        page = PageContent(page_number=1, text=text)
        return ParsedDocument(
            file_path=file_path,
            filename=Path(file_path).name,
            total_pages=1,
            pages=[page],
            full_text=text,
            parse_method="plaintext",
        )
