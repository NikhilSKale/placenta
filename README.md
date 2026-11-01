# 🎓 Placenta — VESIT Placement Experience & Policy Intelligence Platform

**Placenta** is a production-grade, local-first Retrieval-Augmented Generation (RAG) platform built for **Vivekanand Education Society's Institute of Technology (VESIT)**.

It empowers students and placement coordinators to query previous students' placement experiences, retrieve company-specific interview questions, inspect eligibility criteria, compare CTCs, understand official college placement policies, and explore the internal mechanics of the RAG retrieval pipeline with full citation provenance and safety guardrails.

---

## 🌟 Key Capabilities

1. **Strict Evidence-Grounded RAG**: Every factual answer is strictly sourced from indexed student placement experiences or the official VESIT policy handbook. If information is absent, the system explicitly abstains (*"This information is not mentioned in the available placement experience documents for this company/topic."*) rather than hallucinating.
2. **Company & Policy Isolation**: Prevents fact leakage between companies. IVP's assessment pattern is never confused with Network Marvels or ISS Stoxx.
3. **Prompt Injection & Safety Guardrails**: Hardened against prompt injection attacks, jailbreak attempts, and system prompt leaks.
4. **PII Redaction**: Automatically scrubs sensitive personal student information (phone numbers, emails, personal IDs) from inputs and model outputs.
5. **Semantic Caching**: Dense vector caching (`threshold = 0.92`) matches semantically identical questions, delivering instant responses with zero LLM inference overhead.
6. **Intelligent Query Routing**: Dynamically directs questions to appropriate vector stores (`placement_experiences` vs `policy_documents`) and adapts retrieval depth (`top_k`) based on query intent.
7. **Observability & RAG Triad Evaluations**: Real-time telemetry tracking retrieval latency, generation latency, cache hit rates, along with automated **Faithfulness** and **Context Relevance** scoring.
8. **Model Context Protocol (MCP) Server**: Exposes standard tools (`search_placement_experiences`, `query_placement_policy`, `get_company_stats`) for external AI agents and IDEs.
9. **Interactive RAG Explorer**: An educational diagnostic tool visualizing every step:
   $$\text{User Query} \longrightarrow \text{Guardrails} \longrightarrow \text{Semantic Cache} \longrightarrow \text{Query Routing} \longrightarrow \text{Hybrid Retrieval (Dense + BM25)} \longrightarrow \text{Context Assembly} \longrightarrow \text{Grounded Output} \longrightarrow \text{Evals}$$
10. **Self-Contained & Free**: Uses local Sentence Transformers (`BAAI/bge-small-en-v1.5`), ChromaDB, and Ollama (`qwen2.5:3b`). No paid cloud API keys required.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Recharts, React Router v6 |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy, SQLite, Pydantic v2 |
| **Parsing & Extraction** | `pdfplumber`, `PyMuPDF` (fitz), `python-docx` |
| **RAG & Search** | LangChain, ChromaDB (vector database), `rank-bm25` (sparse retrieval), Reciprocal Rank Fusion (RRF) |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (cached locally, 384-dimensional dense vectors) |
| **LLM Inference** | Ollama local inference (`qwen2.5:3b` default) with graceful fallback to cited context preview |
| **Security & Evals** | Regex injection filters, PII redactor, Semantic cosine cache, Faithfulness & Relevance evaluators |
| **Agent Protocols** | FastMCP / Model Context Protocol API tools |

---

## 📂 Project Structure

```text
placenta/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI REST routers (chat, docs, companies, dashboard, rag, policy, observability)
│   │   ├── core/                # Logging, custom exceptions, error handlers
│   │   ├── database/            # SQLAlchemy database engine, session, and init
│   │   ├── models/              # Relational models (Documents, Chunks, Facts, Rounds, Questions)
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   └── services/
│   │       ├── ingestion/       # PDF parsing, structure-aware chunking, file validation
│   │       ├── extraction/      # Rule-based structured fact extractor
│   │       ├── embeddings/      # Sentence-transformers embedder + ChromaDB client
│   │       ├── retrieval/       # Vector store & Hybrid dense + BM25 retriever
│   │       └── rag/             # Guardrails, Semantic Cache, Router, MCP Server, Evals & RAG Engine
│   ├── tests/                   # Automated pytest suite (test_rag.py, test_api.py, test_guardrails_cache_observability.py)
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── .env                     # Local configuration
│   └── .env.example             # Template configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Layout, Topbar, Sidebar, UI components
│   │   ├── pages/               # Overview, Chat, Documents, Companies, Analytics, RAGExplorer, Policy, Settings
│   │   ├── services/api.ts      # Typed REST API client
│   │   ├── types/index.ts       # TypeScript domain models
│   │   └── App.tsx              # Router setup
│   ├── package.json
│   └── vite.config.ts
│
├── placement_experience/        # Local placement experience PDFs (student reports)
├── vesit_policy/                # Official VESIT placement policy documents
├── storage/                     # Persistent SQLite DB and ChromaDB vector store (gitignored)
├── run_backend.bat              # 1-Click Windows launcher for Backend
├── run_frontend.bat             # 1-Click Windows launcher for Frontend
├── .env.example                 # Root configuration template
└── README.md
```

---

## 🔒 Data Privacy Notice (Student Placement Documents)

> [!WARNING]
> **Placement Experience PDF Privacy**:
> Student placement experience PDFs contain personal information such as full names, class divisions, CGPAs, and contact details.
> - In public repositories, do **not** publish identifiable personal records. Add `placement_experience/*.pdf` to `.gitignore` or use anonymized/sample mock PDFs.
> - The application includes automatic **PII Redaction** and **Input/Output Guardrails** to scrub phone numbers, emails, and student identifiers during processing.

---

## 🚀 How to Run the Project

### Windows Quick Start (1-Click)
- **Backend**: Double-click `run_backend.bat` (or run `.\run_backend.bat` in PowerShell).
- **Frontend**: Double-click `run_frontend.bat` (or run `.\run_frontend.bat` in PowerShell).

---

### Manual Setup & Commands

#### Prerequisites
- **Python 3.11 or 3.12** ([Download Python](https://www.python.org/))
- **Node.js v18+** and `npm` ([Download Node.js](https://nodejs.org/))
- *(Optional, for LLM answer generation)* **Ollama**: [Download Ollama](https://ollama.com/) with model `qwen2.5:3b`.

#### Windows (PowerShell / Command Prompt)
1. **Backend setup & run**:
   ```powershell
   cd backend
   # If creating a fresh virtual environment:
   py -3.12 -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend setup & run**:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

#### macOS / Linux
1. **Backend setup & run**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend setup & run**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🧪 Running Automated Tests

Run the full backend test suite covering API endpoints, RAG retrieval, guardrails, semantic cache, and evaluations:

```powershell
cd backend
.\venv\Scripts\activate
pytest
```

---

## 📡 API Endpoints & MCP Tools

- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: `GET /api/health`
- **Chat Endpoint**: `POST /api/chat`
- **RAG Diagnostics Explorer**: `POST /api/rag/explore`
- **Observability & Evals Metrics**: `GET /api/rag/metrics`
- **Clear Semantic Cache**: `POST /api/rag/cache/clear`
- **MCP Tool List**: `GET /api/rag/mcp/tools`
- **MCP Tool Execution**: `POST /api/rag/mcp/call`
