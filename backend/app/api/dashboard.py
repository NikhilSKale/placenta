"""Dashboard analytics endpoints."""
from __future__ import annotations

from collections import Counter
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database.base import get_db
from app.models.models import (
    Document,
    DocumentChunk,
    ExtractedFact,
    InterviewQuestion,
    PlacementExperience,
    RecruitmentRound,
)
from app.services.embeddings.embedder import EmbeddingService

router = APIRouter()

TOPIC_KEYWORDS = {
    "SQL": ["sql", "query", "select", "join", "database"],
    "DBMS": ["dbms", "normalization", "transaction", "acid"],
    "OOP": ["oops", "oop", "inheritance", "polymorphism", "encapsulation", "abstraction", "class", "object"],
    "DSA": ["dsa", "data structure", "algorithm", "array", "linked list", "tree", "graph", "sorting", "searching"],
    "OS": ["os", "operating system", "process", "thread", "deadlock", "memory management"],
    "Networking": ["network", "tcp", "http", "dns", "ip", "protocol", "socket"],
    "Java": ["java", "spring", "jvm", "collections", "multithreading"],
    "Python": ["python", "django", "flask", "pandas", "numpy"],
    "Aptitude": ["aptitude", "quantitative", "logical", "verbal", "reasoning"],
    "Coding": ["coding", "code", "program", "algorithm", "complexity", "leetcode"],
    "AI/ML": ["ai", "machine learning", "deep learning", "neural", "model", "prediction"],
}


def _count_topics_in_text(text: str) -> Counter:
    c = Counter()
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            c[topic] += 1
    return c


@router.get("/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)):
    import httpx
    total_docs = db.query(Document).count()
    placement_count = db.query(Document).filter(Document.doc_type == "placement_experience").count()
    policy_count = db.query(Document).filter(Document.doc_type == "policy").count()

    companies = (
        db.query(Document.company_name)
        .filter(Document.company_name.isnot(None))
        .distinct()
        .all()
    )
    unique_companies = len(companies)

    questions_count = db.query(InterviewQuestion).count()
    chunks_count = db.query(DocumentChunk).count()

    recent_docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )

    # Company overview
    company_map = {}
    for doc in db.query(Document).filter(Document.company_name.isnot(None)).all():
        cn = doc.company_name
        if cn not in company_map:
            company_map[cn] = {
                "id": cn.lower().replace(" ", "_"),
                "name": cn,
                "experience_count": 0,
                "ctc_display": None,
            }
        company_map[cn]["experience_count"] += 1

    # Ollama status
    ollama_ok = False
    try:
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    embedder = EmbeddingService()

    return {
        "total_documents": total_docs,
        "placement_experiences": placement_count,
        "companies": unique_companies,
        "interview_questions": questions_count,
        "indexed_chunks": chunks_count,
        "policy_documents": policy_count,
        "recent_documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "doc_type": d.doc_type,
                "company": d.company_name,
                "student_name": d.student_name,
                "status": d.ingestion_status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in recent_docs
        ],
        "company_overview": list(company_map.values()),
        "suggested_questions": [
            "What was IVP's online assessment pattern?",
            "What technical questions were asked at Network Marvels?",
            "What does the VESIT policy say about placements?",
            "Compare the selection processes of IVP and Network Marvels.",
            "What was the ISS Stoxx assessment pattern?",
            "How did the Nomura hackathon selection work?",
        ],
        "rag_status": {
            "ollama_available": ollama_ok,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.OLLAMA_MODEL,
            "vector_store_size": embedder.get_total_vectors(),
        },
    }


@router.get("/dashboard/analytics")
def dashboard_analytics(db: Session = Depends(get_db)):
    # CTC by company
    ctc_data = []
    exps = db.query(PlacementExperience).filter(PlacementExperience.total_ctc.isnot(None)).all()
    for exp in exps:
        if exp.company_name and exp.total_ctc:
            ctc_data.append({
                "company": exp.company_name,
                "ctc": float(exp.total_ctc),
                "display": f"{exp.total_ctc} LPA",
            })

    # Also check extracted facts for CTC
    if not ctc_data:
        facts = db.query(ExtractedFact).filter(
            ExtractedFact.field_name.in_(["total_ctc", "fixed_ctc"])
        ).all()
        for fact in facts:
            try:
                ctc_val = float(fact.field_value)
                doc = db.query(Document).filter(Document.id == fact.document_id).first()
                if doc and doc.company_name:
                    ctc_data.append({
                        "company": doc.company_name,
                        "ctc": ctc_val,
                        "display": f"{ctc_val} LPA",
                    })
            except (ValueError, TypeError):
                pass

    # Round type distribution
    rounds = db.query(RecruitmentRound).all()
    round_counter = Counter()
    for r in rounds:
        rt = r.round_type or "other"
        label = {
            "online_test": "Online Test",
            "technical_interview": "Technical Interview",
            "hr_interview": "HR Interview",
            "coding": "Coding Round",
            "group_discussion": "Group Discussion",
            "hackathon": "Hackathon",
            "other": "Other",
        }.get(rt, rt.replace("_", " ").title())
        round_counter[label] += 1

    # Topic frequency from interview questions
    questions = db.query(InterviewQuestion).all()
    topic_counter = Counter()
    for q in questions:
        if q.topic:
            topic_counter[q.topic] += 1
        else:
            topic_counter.update(_count_topics_in_text(q.question_text))

    # Also scan raw text for topic mentions
    docs = db.query(Document).filter(Document.raw_text.isnot(None)).all()
    for doc in docs:
        topic_counter.update(_count_topics_in_text(doc.raw_text or ""))

    # Documents per company
    docs_all = db.query(Document).filter(Document.company_name.isnot(None)).all()
    doc_company_counter = Counter(d.company_name for d in docs_all)

    # Document completeness (% of key fields extracted)
    KEY_FIELDS = ["total_ctc", "fixed_ctc", "internship_stipend", "cgpa",
                  "eligible_branches", "selected_count", "company_name"]
    completeness_data = []
    for field in KEY_FIELDS:
        count = db.query(ExtractedFact).filter(
            ExtractedFact.field_name == field,
            ExtractedFact.field_value.isnot(None),
        ).count()
        total = db.query(Document).filter(
            Document.doc_type == "placement_experience"
        ).count()
        pct = round(count / total * 100, 1) if total > 0 else 0
        completeness_data.append({"field": field.replace("_", " ").title(), "percentage": pct})

    return {
        "ctc_by_company": ctc_data,
        "round_distribution": [
            {"name": k, "value": v}
            for k, v in round_counter.most_common(10)
        ],
        "topic_frequency": [
            {"topic": k, "count": v}
            for k, v in topic_counter.most_common(15)
        ],
        "documents_per_company": [
            {"company": k, "count": v}
            for k, v in doc_company_counter.most_common()
        ],
        "document_completeness": completeness_data,
    }

