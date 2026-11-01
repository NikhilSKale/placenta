"""Rule-based structured extractor for placement experience documents."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.models import (
    Document,
    ExtractedFact,
    InterviewQuestion,
    PlacementExperience,
    PolicyClause,
    PreparationResource,
    RecruitmentRound,
)
from app.services.ingestion.pdf_parser import ParsedDocument

logger = get_logger(__name__)

# ── Regex patterns ─────────────────────────────────────────────────────────────

_CTC_PATTERNS = [
    re.compile(r"(?:fixed\s+)?(?:ctc|package|salary|stipend)[:\s]*(?:of\s+)?(?:rs\.?\s*|₹\s*|inr\s*)?(\d+(?:\.\d+)?)\s*(?:lpa|l\.?p\.?a\.?|lakh(?:s)?(?:\s+per\s+annum)?)", re.IGNORECASE),
    re.compile(r"(?:rs\.?\s*|₹\s*)(\d+(?:\.\d+)?)\s*(?:lpa|l\.?p\.?a\.?|lakh)", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:lpa|l\.?p\.?a\.?)\b", re.IGNORECASE),
]

_CGPA_PATTERNS = [
    re.compile(r"cgpa[:\s]+(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"cgpi[:\s]+(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"(?:minimum\s+)?cgpa\s+(?:of\s+)?(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"(\d+\.\d+)\s*(?:cgpa|cgpi|gpa)", re.IGNORECASE),
]

_STUDENT_NAME_PATTERNS = [
    re.compile(r"(?:^|\n)[^\S\r\n]*name[:\s]+([A-Za-z]+(?:[^\S\r\n]+[A-Za-z]+){1,3})", re.IGNORECASE),
    re.compile(r"(?:by|student|submitted\s+by)[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})", re.IGNORECASE),
    re.compile(r"^([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\s*\n", re.MULTILINE),
]

_COMPANY_IN_TEXT = [
    re.compile(r"^([A-Z][A-Za-z0-9\s&.,]{2,50})\s+(?:Placement|Interview)\s+Experience", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?:placed\s+(?:at|in|with)|joining|offer\s+(?:from|by)|selected\s+(?:at|by|for))[:\s]+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|,|\.|$)", re.IGNORECASE),
    re.compile(r"company[:\s]+([A-Za-z0-9\s&.,]+?)(?:\n|,|\.|$)", re.IGNORECASE),
]

_ROUND_HEADERS = re.compile(
    r"(?:^|\n)((?:round\s*\d+|online\s+test|aptitude\s+test|technical\s+(?:interview|round)|hr\s+(?:interview|round)|group\s+discussion|coding\s+(?:test|round)|psychometric\s+test|written\s+test)[:\-–]?\s*.*?)(?=\n)",
    re.IGNORECASE,
)

_QUESTION_PATTERNS = [
    re.compile(r"(?:^|\n)\s*(?:Q\d*[\.:\)]|Question\s*\d*[\.:\)])\s*(.+?)(?=\n\s*(?:Q\d*[\.:\)]|Question\s*\d*|Ans|$))", re.IGNORECASE | re.DOTALL),
    re.compile(r"(?:asked|tell|explain|describe|what|how|why|which|when|where|who)\s+.{10,200}\?", re.IGNORECASE),
]

_PREP_RESOURCES = re.compile(
    r"(?:refer|recommend|suggest|use|practice\s+(?:on|from)?|resource)[:\s]+([A-Za-z0-9\s\+\#\.\-,/]+?)(?:\n|,\.|$)",
    re.IGNORECASE,
)

_STIPEND_PATTERN = re.compile(
    r"stipend[:\s]*(?:rs\.?\s*|₹\s*)?(\d[\d,]*(?:\.\d+)?)\s*(?:per\s+month|/month|pm|p\.m\.)?",
    re.IGNORECASE,
)

_DURATION_PATTERN = re.compile(
    r"(?:internship\s+)?duration[:\s]*(\d+\s*(?:month|week|day)s?)",
    re.IGNORECASE,
)

_SELECTION_COUNT = [
    re.compile(r"(\d+)\s+(?:student|candidate|people|person)s?\s+(?:were\s+)?(?:selected|placed|offered)", re.IGNORECASE),
    re.compile(r"no\.?\s*(?:of)?\s*selected\s*(?:students)?\s*[-:]\s*(\d+)", re.IGNORECASE),
    re.compile(r"selected\s*(?:students)?\s*[-:]\s*(\d+)", re.IGNORECASE),
]


class StructuredExtractor:
    """Rule-based extractor. No LLM required."""

    # ── Filename parsing ────────────────────────────────────────────────────────

    def extract_names_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """Best-effort extraction of (company_name, student_name) from filename."""
        stem = re.sub(r"\.(pdf|docx?|txt|md)$", "", filename, flags=re.IGNORECASE)
        stem = re.sub(r"[_\-]+", " ", stem).strip()

        company: Optional[str] = None
        student: Optional[str] = None

        # Common patterns: "Name_Company_...", "Company - Name", "Name Company Placement Experience"
        known_companies = [
            "Dolat Capital", "Dolat", "TCS Digital", "TCS", "Deloitte", "Nomura", "ISS Stoxx", "ISS", "IVP",
            "Quantiphi", "Network Marvels", "NM", "Stoxx",
        ]
        for kc in known_companies:
            if kc.lower() in stem.lower():
                company = kc
                break

        # Remove common document suffix words like "Placement Experience", "Experience", "Policy", etc.
        cleaned = re.sub(r"\b(placement\s+experience|placement|experience|policy\s+handbook|policy|interview)\b", "", stem, flags=re.IGNORECASE).strip()

        # Student name = first N words that look like a personal name (excluding company name words)
        words = cleaned.split()
        name_words = []
        company_words = [cw.lower() for cw in (company or "").split()]
        for w in words:
            if w.lower() in company_words:
                continue
            if re.match(r"^[A-Z][a-z]+$", w):
                name_words.append(w)
            else:
                break
        if name_words:
            student = " ".join(name_words)

        return company, student

    # ── Full extraction + persistence ─────────────────────────────────────────

    def extract_and_persist(self, parsed: ParsedDocument, document: Document, db: Session) -> None:
        if document.doc_type == "placement_experience":
            self._extract_placement(parsed, document, db)
        elif document.doc_type == "policy":
            self._extract_policy(parsed, document, db)

    # ── Placement experience extraction ───────────────────────────────────────

    def _extract_placement(self, parsed: ParsedDocument, document: Document, db: Session) -> None:
        text = parsed.full_text

        # Extract core facts
        facts: Dict[str, Any] = {}
        facts["company_name"] = self._extract_company(text) or document.company_name
        facts["student_name"] = self._extract_student_name(text) or document.student_name
        facts["cgpa"] = self._extract_cgpa(text)
        ctc_values = self._extract_ctc_values(text)
        facts["fixed_ctc"] = ctc_values.get("fixed")
        facts["total_ctc"] = ctc_values.get("total")
        facts["internship_stipend"] = self._extract_stipend(text)
        facts["internship_duration"] = self._extract_duration(text)
        facts["selected_count"] = self._extract_selection_count(text)

        # Update document-level metadata
        if facts["company_name"] and not document.company_name:
            document.company_name = facts["company_name"]
        if facts["student_name"] and not document.student_name:
            document.student_name = facts["student_name"]

        # Create/update PlacementExperience record
        exp = db.query(PlacementExperience).filter(
            PlacementExperience.document_id == document.id
        ).first()
        if not exp:
            exp = PlacementExperience(document_id=document.id)
            db.add(exp)

        exp.student_name = facts["student_name"]
        exp.company_name = facts["company_name"]
        exp.cgpa = facts["cgpa"]
        exp.fixed_ctc = facts["fixed_ctc"]
        exp.total_ctc = facts["total_ctc"]
        exp.internship_stipend = facts["internship_stipend"]
        exp.internship_duration = facts["internship_duration"]
        exp.selected_count = facts["selected_count"]
        db.flush()

        # Extract rounds
        rounds = self._extract_rounds(text)
        for order, round_data in enumerate(rounds):
            r = RecruitmentRound(
                experience_id=exp.id,
                round_name=round_data["name"],
                round_order=order + 1,
                round_type=round_data.get("type"),
                additional_info=round_data.get("content", "")[:2000],
            )
            db.add(r)
        db.flush()

        # Extract questions
        questions = self._extract_questions(text)
        for q_text in questions:
            q = InterviewQuestion(
                experience_id=exp.id,
                question_text=q_text[:1000],
                question_type=self._classify_question(q_text),
            )
            db.add(q)

        # Extract preparation resources
        resources = self._extract_resources(text)
        for res in resources:
            pr = PreparationResource(
                experience_id=exp.id,
                resource_name=res[:256],
                resource_type="book_or_platform",
            )
            db.add(pr)

        # Persist extracted facts for audit
        self._save_facts(document, facts, db)
        db.commit()

    def _extract_policy(self, parsed: ParsedDocument, document: Document, db: Session) -> None:
        """Extract clauses from policy documents."""
        current_section = None
        current_heading = None
        current_content: List[str] = []
        page_number = 1

        heading_re = re.compile(r"^(\d+(?:\.\d+)*)\s+(.{5,100})$|^([A-Z][A-Z\s]{4,80})$", re.MULTILINE)

        def flush_clause():
            if current_content:
                content = "\n".join(current_content).strip()
                if content:
                    clause = PolicyClause(
                        document_id=document.id,
                        heading=current_heading,
                        content=content[:4000],
                        page_number=page_number,
                        section=current_section,
                    )
                    db.add(clause)

        for page in parsed.pages:
            page_number = page.page_number
            for line in page.text.split("\n"):
                m = heading_re.match(line.strip())
                if m:
                    flush_clause()
                    current_heading = line.strip()
                    current_content = []
                    if m.group(1):
                        current_section = m.group(1)
                else:
                    current_content.append(line)

        flush_clause()
        db.commit()

    # ── Helper extractors ─────────────────────────────────────────────────────

    def _extract_company(self, text: str) -> Optional[str]:
        for pat in _COMPANY_IN_TEXT:
            m = pat.search(text)
            if m:
                return m.group(1).strip()[:100]
        return None

    def _extract_student_name(self, text: str) -> Optional[str]:
        for pat in _STUDENT_NAME_PATTERNS:
            m = pat.search(text)
            if m:
                name = m.group(1).strip()
                if 2 < len(name) < 80:
                    return name
        return None

    def _extract_cgpa(self, text: str) -> Optional[float]:
        for pat in _CGPA_PATTERNS:
            m = pat.search(text)
            if m:
                try:
                    val = float(m.group(1))
                    if 0.0 < val <= 10.0:
                        return val
                except ValueError:
                    pass
        return None

    def _extract_ctc_values(self, text: str) -> Dict[str, Optional[float]]:
        values: Dict[str, Optional[float]] = {"fixed": None, "total": None}
        found = []
        for pat in _CTC_PATTERNS:
            for m in pat.finditer(text):
                try:
                    val = float(m.group(1))
                    if 0 < val < 500:  # sanity: LPA should be < 500
                        found.append(val)
                except ValueError:
                    pass
        if found:
            values["fixed"] = min(found)
            values["total"] = max(found)
        return values

    def _extract_stipend(self, text: str) -> Optional[float]:
        m = _STIPEND_PATTERN.search(text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
        return None

    def _extract_duration(self, text: str) -> Optional[str]:
        m = _DURATION_PATTERN.search(text)
        return m.group(1).strip() if m else None

    def _extract_selection_count(self, text: str) -> Optional[int]:
        for pat in _SELECTION_COUNT:
            m = pat.search(text)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass
        return None

    def _extract_rounds(self, text: str) -> List[Dict]:
        rounds = []
        for m in _ROUND_HEADERS.finditer(text):
            name = m.group(1).strip()
            # Get content up to the next round header
            start = m.end()
            next_m = _ROUND_HEADERS.search(text, start)
            end = next_m.start() if next_m else start + 2000
            content = text[start:end].strip()
            round_type = self._classify_round_type(name)
            rounds.append({"name": name, "type": round_type, "content": content})
        return rounds

    def _classify_round_type(self, name: str) -> str:
        name_l = name.lower()
        if "online" in name_l or "aptitude" in name_l or "test" in name_l:
            return "online_test"
        if "technical" in name_l:
            return "technical_interview"
        if "hr" in name_l:
            return "hr_interview"
        if "coding" in name_l:
            return "coding"
        if "group" in name_l or "gd" in name_l:
            return "group_discussion"
        return "other"

    def _extract_questions(self, text: str) -> List[str]:
        questions = []
        seen = set()
        for pat in _QUESTION_PATTERNS:
            for m in pat.finditer(text):
                q = m.group(0).strip()
                if q and q not in seen and len(q) > 15:
                    seen.add(q)
                    questions.append(q)
        return questions[:100]  # cap

    def _classify_question(self, text: str) -> str:
        text_l = text.lower()
        if any(k in text_l for k in ["code", "program", "algorithm", "complexity", "implement"]):
            return "coding"
        if any(k in text_l for k in ["tell me about", "yourself", "strengths", "weakness", "why"]):
            return "hr"
        if any(k in text_l for k in ["dbms", "os", "network", "sql", "pointer", "oops", "class", "inheritance"]):
            return "technical_cs"
        return "technical"

    def _extract_resources(self, text: str) -> List[str]:
        resources = []
        known = [
            "geeksforgeeks", "leetcode", "hackerrank", "interviewbit", "hackerearth",
            "codechef", "codeforces", "coursera", "udemy", "nptel", "youtube",
            "gate", "cprogramming",
        ]
        text_l = text.lower()
        for res in known:
            if res in text_l:
                resources.append(res)
        # Also regex
        for m in _PREP_RESOURCES.finditer(text):
            val = m.group(1).strip()
            if val and val not in resources:
                resources.append(val)
        return resources[:20]

    def _save_facts(self, document: Document, facts: Dict, db: Session) -> None:
        # Remove existing facts for this document
        db.query(ExtractedFact).filter(ExtractedFact.document_id == document.id).delete()
        for field_name, field_value in facts.items():
            if field_value is not None:
                fact = ExtractedFact(
                    document_id=document.id,
                    field_name=field_name,
                    field_value=str(field_value),
                    extraction_method="rule_based",
                )
                db.add(fact)
