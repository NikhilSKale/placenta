import type {
  ChatRequest,
  ChatSession,
  ChatMessage,
  Document,
  DocumentChunk,
  ExtractedFact,
  Company,
  DashboardOverview,
  DashboardAnalytics,
  RAGExploreResult,
  RetrievedChunk,
  PolicySection,
  AppSettings,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  // Health
  health: () =>
    fetch(`${API_BASE}/health`).then((r) => handleResponse<{ status: string; ollama: boolean }>(r)),

  // Chat
  chat: (body: ChatRequest) =>
    fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((r) =>
      handleResponse<{ message: ChatMessage; session_id: string }>(r)
    ),

  getSessions: () =>
    fetch(`${API_BASE}/chats`).then((r) => handleResponse<ChatSession[]>(r)),

  getSession: (id: string) =>
    fetch(`${API_BASE}/chats/${id}`).then((r) =>
      handleResponse<{ session: ChatSession; messages: ChatMessage[] }>(r)
    ),

  deleteSession: (id: string) =>
    fetch(`${API_BASE}/chats/${id}`, { method: 'DELETE' }).then((r) =>
      handleResponse<{ success: boolean }>(r)
    ),

  // Documents
  getDocuments: () =>
    fetch(`${API_BASE}/documents`).then((r) => handleResponse<Document[]>(r)),

  uploadDocument: (file: File, docType: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', docType)
    return fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: fd,
    }).then((r) => handleResponse<Document>(r))
  },

  getDocument: (id: string) =>
    fetch(`${API_BASE}/documents/${id}`).then((r) =>
      handleResponse<Document>(r)
    ),

  getDocumentFacts: (id: string) =>
    fetch(`${API_BASE}/documents/${id}/facts`).then((r) =>
      handleResponse<ExtractedFact[]>(r)
    ),

  getDocumentChunks: (id: string) =>
    fetch(`${API_BASE}/documents/${id}/chunks`).then((r) =>
      handleResponse<DocumentChunk[]>(r)
    ),

  reindexDocument: (id: string) =>
    fetch(`${API_BASE}/documents/${id}/reindex`, { method: 'POST' }).then((r) =>
      handleResponse<{ success: boolean }>(r)
    ),

  deleteDocument: (id: string) =>
    fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' }).then((r) =>
      handleResponse<{ success: boolean }>(r)
    ),

  // Companies
  getCompanies: () =>
    fetch(`${API_BASE}/companies`).then((r) => handleResponse<Company[]>(r)),

  getCompany: (id: string) =>
    fetch(`${API_BASE}/companies/${id}`).then((r) =>
      handleResponse<Company>(r)
    ),

  // Dashboard
  getDashboardOverview: () =>
    fetch(`${API_BASE}/dashboard/overview`).then((r) =>
      handleResponse<DashboardOverview>(r)
    ),

  getDashboardAnalytics: () =>
    fetch(`${API_BASE}/dashboard/analytics`).then((r) =>
      handleResponse<DashboardAnalytics>(r)
    ),

  // RAG
  ragRetrieve: (query: string, filters?: object) =>
    fetch(`${API_BASE}/rag/retrieve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...filters }),
    }).then((r) => handleResponse<RetrievedChunk[]>(r)),

  ragExplore: (query: string, filters?: object) =>
    fetch(`${API_BASE}/rag/explore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...filters }),
    }).then((r) => handleResponse<RAGExploreResult>(r)),

  ragStatus: () =>
    fetch(`${API_BASE}/rag/status`).then((r) =>
      handleResponse<{
        ollama_available: boolean
        embedding_model: string
        llm_model: string
        vector_store_size: number
      }>(r)
    ),

  // Policy
  getPolicySections: () =>
    fetch(`${API_BASE}/policy/sections`).then((r) =>
      handleResponse<PolicySection[]>(r)
    ),

  // Settings
  getSettings: () =>
    fetch(`${API_BASE}/settings`).then((r) =>
      handleResponse<AppSettings>(r)
    ),

  saveSettings: (settings: Partial<AppSettings>) =>
    fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }).then((r) => handleResponse<AppSettings>(r)),
}
