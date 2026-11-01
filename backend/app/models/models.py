"""SQLAlchemy ORM models for Placenta."""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


# ── Document ──────────────────────────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False, default="placement_experience")
    company_name: Mapped[Optional[str]] = mapped_column(String(256))
    student_name: Mapped[Optional[str]] = mapped_column(String(256))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    num_pages: Mapped[Optional[int]] = mapped_column(Integer)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    extraction_status: Mapped[str] = mapped_column(String(32), default="pending")
    ingestion_status: Mapped[str] = mapped_column(String(32), default="pending")
    indexed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    raw_text: Mapped[Optional[str]] = mapped_column(Text)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    placement_experience: Mapped[Optional["PlacementExperience"]] = relationship(
        "PlacementExperience", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(
        "ExtractedFact", back_populates="document", cascade="all, delete-orphan"
    )
    policy_clauses: Mapped[list["PolicyClause"]] = relationship(
        "PolicyClause", back_populates="document", cascade="all, delete-orphan"
    )
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(
        "IngestionJob", back_populates="document", cascade="all, delete-orphan"
    )


# ── DocumentChunk ─────────────────────────────────────────────────────────────

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(256))

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")


# ── PlacementExperience ────────────────────────────────────────────────────────

class PlacementExperience(Base):
    __tablename__ = "placement_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), unique=True, nullable=False)
    student_name: Mapped[Optional[str]] = mapped_column(String(256))
    department: Mapped[Optional[str]] = mapped_column(String(128))
    cgpa: Mapped[Optional[float]] = mapped_column(Float)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    company_name: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    job_role: Mapped[Optional[str]] = mapped_column(String(256))
    job_location: Mapped[Optional[str]] = mapped_column(String(256))
    fixed_ctc: Mapped[Optional[float]] = mapped_column(Float)
    total_ctc: Mapped[Optional[float]] = mapped_column(Float)
    internship_stipend: Mapped[Optional[float]] = mapped_column(Float)
    internship_duration: Mapped[Optional[str]] = mapped_column(String(128))
    ppo_opportunity: Mapped[Optional[bool]] = mapped_column(Boolean)
    eligible_branches: Mapped[Optional[str]] = mapped_column(Text)
    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text)
    drive_date: Mapped[Optional[str]] = mapped_column(String(128))
    selected_count: Mapped[Optional[int]] = mapped_column(Integer)
    appeared_count: Mapped[Optional[int]] = mapped_column(Integer)
    shortlisted_count: Mapped[Optional[int]] = mapped_column(Integer)

    document: Mapped["Document"] = relationship("Document", back_populates="placement_experience")
    recruitment_rounds: Mapped[list["RecruitmentRound"]] = relationship(
        "RecruitmentRound", back_populates="experience", cascade="all, delete-orphan"
    )
    interview_questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion", back_populates="experience", cascade="all, delete-orphan"
    )
    preparation_resources: Mapped[list["PreparationResource"]] = relationship(
        "PreparationResource", back_populates="experience", cascade="all, delete-orphan"
    )


# ── RecruitmentRound ──────────────────────────────────────────────────────────

class RecruitmentRound(Base):
    __tablename__ = "recruitment_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experience_id: Mapped[int] = mapped_column(Integer, ForeignKey("placement_experiences.id"), nullable=False, index=True)
    round_name: Mapped[str] = mapped_column(String(256), nullable=False)
    round_order: Mapped[int] = mapped_column(Integer, default=0)
    round_type: Mapped[Optional[str]] = mapped_column(String(64))
    date: Mapped[Optional[str]] = mapped_column(String(64))
    duration: Mapped[Optional[str]] = mapped_column(String(128))
    mode: Mapped[Optional[str]] = mapped_column(String(64))
    num_questions: Mapped[Optional[int]] = mapped_column(Integer)
    topics: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[Optional[str]] = mapped_column(String(64))
    selected_count: Mapped[Optional[int]] = mapped_column(Integer)
    additional_info: Mapped[Optional[str]] = mapped_column(Text)

    experience: Mapped["PlacementExperience"] = relationship("PlacementExperience", back_populates="recruitment_rounds")
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion", back_populates="round", cascade="all, delete-orphan"
    )


# ── InterviewQuestion ─────────────────────────────────────────────────────────

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experience_id: Mapped[int] = mapped_column(Integer, ForeignKey("placement_experiences.id"), nullable=False, index=True)
    round_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recruitment_rounds.id"))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[Optional[str]] = mapped_column(String(64))
    topic: Mapped[Optional[str]] = mapped_column(String(128))
    programming_language: Mapped[Optional[str]] = mapped_column(String(64))
    concepts: Mapped[Optional[str]] = mapped_column(Text)

    experience: Mapped["PlacementExperience"] = relationship("PlacementExperience", back_populates="interview_questions")
    round: Mapped[Optional["RecruitmentRound"]] = relationship("RecruitmentRound", back_populates="questions")


# ── PreparationResource ───────────────────────────────────────────────────────

class PreparationResource(Base):
    __tablename__ = "preparation_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experience_id: Mapped[int] = mapped_column(Integer, ForeignKey("placement_experiences.id"), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(64))
    resource_name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    experience: Mapped["PlacementExperience"] = relationship("PlacementExperience", back_populates="preparation_resources")


# ── ExtractedFact ─────────────────────────────────────────────────────────────

class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_value: Mapped[Optional[str]] = mapped_column(Text)
    evidence_status: Mapped[str] = mapped_column(String(32), default="extracted")
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    evidence_text: Mapped[Optional[str]] = mapped_column(Text)
    extraction_method: Mapped[str] = mapped_column(String(64), default="rule_based")
    is_manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)

    document: Mapped["Document"] = relationship("Document", back_populates="extracted_facts")


# ── PolicyClause ──────────────────────────────────────────────────────────────

class PolicyClause(Base):
    __tablename__ = "policy_clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    clause_number: Mapped[Optional[str]] = mapped_column(String(64))
    heading: Mapped[Optional[str]] = mapped_column(String(512))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    section: Mapped[Optional[str]] = mapped_column(String(256))

    document: Mapped["Document"] = relationship("Document", back_populates="policy_clauses")


# ── ChatSession ───────────────────────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(512), default="New Chat")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    filter_company: Mapped[Optional[str]] = mapped_column(String(256))
    filter_doc_type: Mapped[Optional[str]] = mapped_column(String(64))

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


# ── ChatMessage ───────────────────────────────────────────────────────────────

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    sources_json: Mapped[Optional[str]] = mapped_column(Text)
    retrieval_metadata_json: Mapped[Optional[str]] = mapped_column(Text)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


# ── IngestionJob ──────────────────────────────────────────────────────────────

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    warnings_json: Mapped[Optional[str]] = mapped_column(Text)

    document: Mapped["Document"] = relationship("Document", back_populates="ingestion_jobs")
