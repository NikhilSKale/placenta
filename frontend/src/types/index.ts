// ============================================================
// Types for Placenta — VESIT Placement Intelligence Platform
// ============================================================

// Document types
export type DocStatus = 'completed' | 'indexed' | 'processing' | 'failed' | 'pending' | 'partial';
export type DocType = 'placement_experience' | 'policy' | 'experience' | 'company' | 'other';

export interface Document {
  id: string;
  filename: string;
  doc_type: DocType | string;
  company?: string;
  company_name?: string;
  student_name?: string;
  year?: number;
  pages?: number;
  num_pages?: number;
  chunk_count?: number;
  num_chunks?: number;
  status: DocStatus | string;
  ingestion_status?: string;
  extraction_status?: string;
  indexed_at?: string;
  created_at: string;
  size_bytes?: number;
  raw_text?: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  page_number?: number;
  metadata?: Record<string, unknown>;
  embedding_id?: string;
}

export interface ExtractedFact {
  id?: string;
  field: string;
  field_name?: string;
  value: string;
  field_value?: string;
  evidence?: string;
  evidence_text?: string;
  confidence?: number;
  evidence_status?: string;
  source_page?: number;
  extraction_method?: string;
  is_manually_corrected?: boolean;
}

// Chat types
export interface SourceCitation {
  document_id: string;
  filename: string;
  company?: string;
  page?: number;
  chunk_id?: string;
  snippet: string;
  score?: number;
  section?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  suggested_questions?: string[];
  created_at: string;
  error?: boolean;
  retrieval_metadata?: Record<string, unknown>;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string | number;
  filter_company?: string;
  filter_doc_type?: string;
  top_k?: number;
}

// Company types
export interface RecruitmentRound {
  round_number: number;
  round_name: string;
  description?: string;
  duration?: string;
  questions?: string[];
  round_type?: string;
  topics?: string;
  difficulty?: string;
  selected_count?: number;
  additional_info?: string;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  round?: string;
  topic?: string;
  difficulty?: 'easy' | 'medium' | 'hard' | string;
  source_doc?: string;
  question_type?: string;
  programming_language?: string;
  concepts?: string;
}

export interface PlacementExperience {
  id: string;
  student_name?: string;
  company: string;
  year?: number;
  ctc?: number;
  ctc_display?: string;
  role?: string;
  rounds?: RecruitmentRound[];
  tips?: string[];
  overall_difficulty?: string;
  document_id?: string;
}

export interface Company {
  id: string;
  name: string;
  experience_count: number;
  student_count?: number;
  ctc_min?: number;
  ctc_max?: number;
  ctc_display?: string;
  roles?: string[];
  years?: number[];
  questions?: InterviewQuestion[];
  experiences?: PlacementExperience[];
  document_ids?: string[];
}

// Dashboard types
export interface StatCard {
  label: string;
  value: number | string;
  icon?: string;
  change?: number;
}

export interface DashboardOverview {
  total_documents: number;
  placement_experiences: number;
  companies: number;
  interview_questions: number;
  indexed_chunks: number;
  policy_documents: number;
  recent_documents: Document[];
  company_overview: Company[];
  suggested_questions?: string[];
  rag_status?: {
    ollama_available: boolean;
    embedding_model: string;
    llm_model: string;
    vector_store_size?: number;
  };
}

export interface CTCData {
  company: string;
  ctc: number;
  display: string;
}

export interface RoundDistribution {
  name: string;
  value: number;
}

export interface TopicFrequency {
  topic: string;
  count: number;
}

export interface CompanyDocCount {
  company: string;
  count: number;
}

export interface CompletenessData {
  field: string;
  percentage: number;
}

export interface DashboardAnalytics {
  ctc_by_company: CTCData[];
  round_distribution: RoundDistribution[];
  topic_frequency: TopicFrequency[];
  documents_per_company: CompanyDocCount[];
  document_completeness: CompletenessData[];
}

// RAG types
export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  text: string;
  score: number;
  metadata?: Record<string, unknown>;
  company?: string;
  page?: number;
}

export interface RAGStep {
  step: string;
  title: string;
  data: unknown;
  latency_ms?: number;
}

export interface RAGExploreResult {
  query: string;
  steps: RAGStep[];
  retrieved_chunks: RetrievedChunk[];
  reranked_chunks: RetrievedChunk[];
  context: string;
  answer: string;
  citations: SourceCitation[];
  diagnostics: {
    total_latency_ms: number;
    retrieval_latency_ms: number;
    generation_latency_ms: number;
    chunk_count: number;
    confidence?: number;
    detected_company?: string;
    detected_topics?: string[];
  };
}

// Policy types
export interface PolicySection {
  id: string;
  heading: string;
  content: string;
  document_id?: string;
  page?: number;
}

// Settings types
export interface AppSettings {
  ollama_base_url: string;
  ollama_model: string;
  embedding_model: string;
  top_k: number;
  similarity_threshold: number;
  theme: 'dark' | 'light';
}
