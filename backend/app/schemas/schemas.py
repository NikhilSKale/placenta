"""Pydantic schemas for request/response validation."""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Shared ─────────────────────────────────────────────────────────────────────

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Document schemas ──────────────────────────────────────────────────────────

class DocumentOut(OrmBase):
    id: int
    filename: str
    doc_type: str
    company_name: Optional[str]
    student_name: Optional[str]
    year: Optional[int]
    num_pages: Optional[int]
    num_chunks: int
    extraction_status: str
    ingestion_status: str
    indexed_at: Optional[datetime.datetime]
    created_at: datetime.datetime


class DocumentDetail(DocumentOut):
    raw_text: Optional[str]


class ExtractedFactOut(OrmBase):
    id: int
    field_name: str
    field_value: Optional[str]
    evidence_status: str
    source_page: Optional[int]
    evidence_text: Optional[str]
    extraction_method: str
    is_manually_corrected: bool


class DocumentChunkOut(OrmBase):
    id: int
    chunk_index: int
    text: str
    chunk_metadata_json: Optional[str]
    embedding_id: Optional[str]


# ── Placement experience schemas ───────────────────────────────────────────────

class RecruitmentRoundOut(OrmBase):
    id: int
    round_name: str
    round_order: int
    round_type: Optional[str]
    date: Optional[str]
    duration: Optional[str]
    mode: Optional[str]
    num_questions: Optional[int]
    topics: Optional[str]
    difficulty: Optional[str]
    selected_count: Optional[int]
    additional_info: Optional[str]


class InterviewQuestionOut(OrmBase):
    id: int
    question_text: str
    question_type: Optional[str]
    topic: Optional[str]
    programming_language: Optional[str]
    concepts: Optional[str]
    round_id: Optional[int]


class PreparationResourceOut(OrmBase):
    id: int
    resource_type: Optional[str]
    resource_name: str
    description: Optional[str]


class PlacementExperienceOut(OrmBase):
    id: int
    student_name: Optional[str]
    department: Optional[str]
    cgpa: Optional[float]
    graduation_year: Optional[int]
    company_name: Optional[str]
    job_role: Optional[str]
    job_location: Optional[str]
    fixed_ctc: Optional[float]
    total_ctc: Optional[float]
    internship_stipend: Optional[float]
    internship_duration: Optional[str]
    ppo_opportunity: Optional[bool]
    eligible_branches: Optional[str]
    eligibility_criteria: Optional[str]
    drive_date: Optional[str]
    selected_count: Optional[int]
    appeared_count: Optional[int]
    shortlisted_count: Optional[int]
    recruitment_rounds: List[RecruitmentRoundOut] = []
    interview_questions: List[InterviewQuestionOut] = []
    preparation_resources: List[PreparationResourceOut] = []


# ── Company schemas ───────────────────────────────────────────────────────────

class CompanySummary(BaseModel):
    company_name: str
    document_count: int
    avg_ctc: Optional[float]
    max_ctc: Optional[float]
    roles: List[str]


class CompanyDetail(CompanySummary):
    experiences: List[PlacementExperienceOut]


# ── Chat schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[int] = None
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None


class SourceCitation(BaseModel):
    document_id: int
    filename: str
    student_name: Optional[str]
    company_name: Optional[str]
    page_number: Optional[int]
    chunk_text: str
    relevance_score: float


class ChatResponse(BaseModel):
    session_id: int
    message_id: int
    answer: str
    sources: List[SourceCitation]
    retrieval_metadata: Dict[str, Any] = {}


class ChatMessageOut(OrmBase):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime.datetime
    sources_json: Optional[str]
    retrieval_metadata_json: Optional[str]


class ChatSessionOut(OrmBase):
    id: int
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    filter_company: Optional[str]
    filter_doc_type: Optional[str]


class ChatSessionDetail(ChatSessionOut):
    messages: List[ChatMessageOut]


# ── RAG schemas ───────────────────────────────────────────────────────────────

class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = {}


class RetrieveResponse(BaseModel):
    query: str
    chunks: List[RetrievedChunk]
    total_retrieved: int


class ExploreRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filter_company: Optional[str] = None
    filter_doc_type: Optional[str] = None


class ExploreResponse(BaseModel):
    query: str
    query_intent: str
    entities_extracted: Dict[str, Any]
    retrieval_steps: List[Dict[str, Any]]
    retrieved_chunks: List[RetrievedChunk]
    prompt_preview: str
    answer: str
    sources: List[SourceCitation]


# ── Policy schemas ────────────────────────────────────────────────────────────

class PolicyClauseOut(OrmBase):
    id: int
    clause_number: Optional[str]
    heading: Optional[str]
    content: str
    page_number: Optional[int]
    section: Optional[str]


# ── Dashboard schemas ─────────────────────────────────────────────────────────

class DashboardOverview(BaseModel):
    total_documents: int
    total_placement_experiences: int
    total_companies: int
    total_chunks: int
    total_questions: int
    avg_ctc: Optional[float]
    indexed_documents: int
    pending_documents: int


class CTCDataPoint(BaseModel):
    company: str
    avg_ctc: Optional[float]
    max_ctc: Optional[float]
    count: int


class RoundDistribution(BaseModel):
    round_type: str
    count: int


class TopicCount(BaseModel):
    topic: str
    count: int


class DashboardAnalytics(BaseModel):
    ctc_by_company: List[CTCDataPoint]
    round_distribution: List[RoundDistribution]
    top_topics: List[TopicCount]
    documents_by_type: Dict[str, int]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    ollama_model: str
    vector_db_status: str
    total_vectors: int
    database_status: str
    version: str = "1.0.0"


# ── Ingestion Job ─────────────────────────────────────────────────────────────

class IngestionJobOut(OrmBase):
    id: int
    document_id: int
    status: str
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
    error_message: Optional[str]
    warnings_json: Optional[str]
