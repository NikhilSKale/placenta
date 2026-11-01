"""Companies API endpoints."""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.models import (
    Document,
    InterviewQuestion,
    PlacementExperience,
    RecruitmentRound,
)

router = APIRouter()

# Canonical company name normalization
COMPANY_ALIASES = {
    "NM": "Network Marvels",
    "ISS": "ISS Stoxx",
    "IVP": "IVP",
    "TCS Digital": "TCS Digital",
    "TCS": "TCS",
}


def _normalize_company(name: str) -> str:
    if not name:
        return name
    return COMPANY_ALIASES.get(name.strip(), name.strip())


@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    # Group documents by company
    docs = db.query(Document).filter(Document.company_name.isnot(None)).all()
    company_map: dict = {}
    for doc in docs:
        cn = _normalize_company(doc.company_name or "Unknown")
        if cn not in company_map:
            company_map[cn] = {
                "id": cn.lower().replace(" ", "_"),
                "name": cn,
                "experience_count": 0,
                "student_count": 0,
                "ctc_min": None,
                "ctc_max": None,
                "ctc_display": None,
                "roles": [],
                "years": [],
                "document_ids": [],
            }
        company_map[cn]["document_ids"].append(str(doc.id))
        company_map[cn]["experience_count"] += 1
        if doc.student_name:
            company_map[cn]["student_count"] += 1
        if doc.year and doc.year not in company_map[cn]["years"]:
            company_map[cn]["years"].append(doc.year)

        # Fetch placement experience for CTC
        exp = (
            db.query(PlacementExperience)
            .filter(PlacementExperience.document_id == doc.id)
            .first()
        )
        if exp:
            if exp.job_role and exp.job_role not in company_map[cn]["roles"]:
                company_map[cn]["roles"].append(exp.job_role)
            if exp.total_ctc:
                ctc = exp.total_ctc
                if company_map[cn]["ctc_min"] is None or ctc < company_map[cn]["ctc_min"]:
                    company_map[cn]["ctc_min"] = ctc
                if company_map[cn]["ctc_max"] is None or ctc > company_map[cn]["ctc_max"]:
                    company_map[cn]["ctc_max"] = ctc

    for cn, data in company_map.items():
        if data["ctc_min"] is not None:
            if data["ctc_min"] == data["ctc_max"]:
                data["ctc_display"] = f"{data['ctc_max']} LPA"
            else:
                data["ctc_display"] = f"{data['ctc_min']}–{data['ctc_max']} LPA"

    return list(company_map.values())


@router.get("/companies/{company_id}")
def get_company(company_id: str, db: Session = Depends(get_db)):
    # company_id is slug: e.g. "ivp", "network_marvels"
    company_name = company_id.replace("_", " ").title()

    # Try to find matching documents
    docs = db.query(Document).filter(Document.company_name.isnot(None)).all()
    matching_docs = [
        d for d in docs
        if (d.company_name or "").lower().replace(" ", "_") == company_id.lower()
        or (d.company_name or "").lower() == company_name.lower()
        or company_id.lower() in (d.company_name or "").lower()
    ]

    if not matching_docs:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")

    canonical_name = matching_docs[0].company_name

    experiences = []
    all_rounds = []
    all_questions = []
    all_tips = []

    for doc in matching_docs:
        exp = (
            db.query(PlacementExperience)
            .filter(PlacementExperience.document_id == doc.id)
            .first()
        )
        exp_data = {
            "id": str(doc.id),
            "student_name": doc.student_name,
            "company": canonical_name,
            "year": doc.year,
            "document_id": str(doc.id),
            "filename": doc.filename,
        }
        if exp:
            exp_data.update({
                "ctc": exp.total_ctc,
                "ctc_display": f"{exp.total_ctc} LPA" if exp.total_ctc else None,
                "fixed_ctc": exp.fixed_ctc,
                "internship_stipend": exp.internship_stipend,
                "role": exp.job_role,
                "department": exp.department,
                "cgpa": exp.cgpa,
                "eligible_branches": exp.eligible_branches,
                "eligibility_criteria": exp.eligibility_criteria,
                "ppo_opportunity": exp.ppo_opportunity,
            })

            # Rounds
            rounds = (
                db.query(RecruitmentRound)
                .filter(RecruitmentRound.experience_id == exp.id)
                .order_by(RecruitmentRound.round_order.asc())
                .all()
            )
            exp_data["rounds"] = [
                {
                    "round_number": r.round_order,
                    "round_name": r.round_name,
                    "round_type": r.round_type,
                    "duration": r.duration,
                    "num_questions": r.num_questions,
                    "topics": r.topics,
                    "difficulty": r.difficulty,
                    "selected_count": r.selected_count,
                    "additional_info": r.additional_info,
                }
                for r in rounds
            ]
            all_rounds.extend(exp_data["rounds"])

            # Interview questions
            questions = (
                db.query(InterviewQuestion)
                .filter(InterviewQuestion.experience_id == exp.id)
                .all()
            )
            exp_data["questions"] = [
                {
                    "id": str(q.id),
                    "question": q.question_text,
                    "question_type": q.question_type,
                    "topic": q.topic,
                    "programming_language": q.programming_language,
                    "concepts": q.concepts,
                }
                for q in questions
            ]
            all_questions.extend(exp_data["questions"])

        experiences.append(exp_data)

    return {
        "id": company_id,
        "name": canonical_name,
        "experience_count": len(matching_docs),
        "document_ids": [str(d.id) for d in matching_docs],
        "experiences": experiences,
        "all_rounds": all_rounds,
        "all_questions": all_questions,
    }

