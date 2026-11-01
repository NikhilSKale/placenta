# 🎓 Placenta — VESIT Placement Experience & Policy Intelligence Platform

**Placenta** is a production-grade, local-first Retrieval-Augmented Generation (RAG) platform built for **Vivekanand Education Society's Institute of Technology (VESIT)**.

It empowers students and placement coordinators to query previous students' placement experiences, retrieve company-specific interview questions, inspect eligibility criteria, compare CTCs, understand official college placement policies, and explore the internal mechanics of the RAG retrieval pipeline with full citation provenance.

---

## 🌟 Key Capabilities

1. **Strict Evidence-Grounded RAG**: Every factual answer is strictly sourced from indexed student placement experiences or the official VESIT policy handbook. If information is absent, the system explicitly abstains rather than hallucinating.
2. **Company & Policy Isolation**: Prevents fact leakage between companies. IVP's assessment pattern is never confused with Network Marvels or ISS Stoxx.
3. **Structured Fact Extraction & Provenance**: Automatically extracts compensation (fixed CTC, stipend, conditional PPOs), CGPA, selection rounds, and questions asked with page-level citations.
4. **Dynamic Analytics Dashboard**: Aggregates real metrics directly from extracted records (CTC comparisons, round type distributions, topic frequency, document completeness).
5. **Interactive RAG Explorer**: An educational diagnostic tool visualizing every step:
   $$\text{User Query} \longrightarrow \text{Query Analysis} \longrightarrow \text{Hybrid Retrieval (Dense + BM25)} \longrightarrow \text{RRF Merge} \longrightarrow \text{Context Assembly} \longrightarrow \text{Grounded Output}$$
6. **Self-Contained & Free**: Uses local Sentence Transformers (`BAAI/bge-small-en-v1.5`), ChromaDB, and Ollama (`qwen2.5:3b`). No paid cloud API keys required.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Recharts, React Router v6 |
| **Backend** | Python 3.14 / 3.11+, FastAPI, SQLAlchemy, SQLite, Pydantic v2 |
| **Parsing & Extraction** | `pdfplumber`, `PyMuPDF` (fitz), `python-docx` |
| **RAG & Search** | LangChain, ChromaDB (vector database), `rank-bm25` (sparse retrieval), Reciprocal Rank Fusion (RRF) |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (cached locally, 384-dimensional dense vectors) |
| **LLM Inference** | Ollama local inference (`qwen2.5:3b` default) with graceful fallback to cited context preview |

---

## 📂 Project Structure

```text
project/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI REST routers (chat, docs, companies, dashboard, rag, policy)
│   │   ├── core/                # Logging, custom exceptions, error handlers
│   │   ├── database/            # SQLAlchemy database engine, session, and init
│   │   ├── models/              # Relational models (Documents, Chunks, Facts, Rounds, Questions)
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   └── services/
│   │       ├── ingestion/       # PDF parsing, structure-aware chunking, file validation
│   │       ├── extraction/      # Rule-based structured fact extractor
│   │       ├── embeddings/      # Sentence-transformers embedder + ChromaDB client
│   │       ├── retrieval/       # Vector store & Hybrid dense + BM25 retriever
│   │       └── rag/             # Query classifier, grounded generation & citation builder
│   ├── tests/                   # Pytest automated test suite (test_rag.py, test_api.py)
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Backend configuration
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
├── placement_experience/        # Original student placement experience PDFs
├── vesit_policy/                # Official VESIT placement policy PDF
├── storage/                     # Persistent SQLite DB and ChromaDB vector store
├── .env.example
└── README.md
```

---

## 🚀 How to Run the Project

**Note:** The repository includes appropriate `.gitignore` files for both backend and frontend. Ensure you do not commit generated files such as virtual environments, `node_modules`, the `storage/` directory, or any generated `.env` files.

---
## 📦 Repository Setup (GitHub)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NikhilSKale/placenta.git
   cd placenta
   ```
2. **Install backend dependencies** (inside `project/backend`):
   ```bash
   cd project/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Install frontend dependencies** (inside `project/frontend`):
   ```bash
   cd ../frontend
   npm install
   ```
4. **Run the application** as described in the original "How to Run the Project" section.

The `.gitignore` files ensure that sensitive or large generated artefacts are not tracked:
- `project/.gitignore` – top‑level ignores OS artefacts, the `storage/` directory, and IDE files.
- `project/backend/.gitignore` – Python‑specific ignores (`venv/`, `__pycache__/`, `.env`, database files).
- `project/frontend/.gitignore` – Node‑specific ignores (`node_modules/`, `dist/`, local env files).

Feel free to adjust the ignore patterns if you add other generated directories.


### Prerequisites

- **Python 3.10+** (Python 3.11–3.14 supported)
- **Node.js v18+** and `npm`
- *(Optional, for generative AI answers)* **Ollama**: [Download Ollama](https://ollama.com/)

---

### Step 1: Start the Backend Server

1. Open a terminal and navigate to `project/backend`:
   ```bash
   cd project/backend
   ```

2. Activate the virtual environment (created during setup):
   ```bash
   source venv/bin/activate
   ```
   *(If creating a fresh environment: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`)*

3. Start the FastAPI backend server:
   ```bash
   PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Verify the backend is operational:
   - **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

> **Note on Initial Run**: On startup, the backend automatically scans `project/placement_experience/` and `project/vesit_policy/`, parses all PDFs, extracts structured facts, generates embeddings, and saves them to `storage/application.db` and ChromaDB.

---

### Step 2: Start the Frontend Application

1. Open a second terminal and navigate to `project/frontend`:
   ```bash
   cd project/frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Launch the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser at:
   👉 **[http://localhost:5173](http://localhost:5173)**

---

### Step 3: (Optional) Start Ollama for Local LLM Synthesis

Placenta includes a graceful fallback that displays retrieved evidence directly even without an active LLM. To enable complete natural language synthesis:

1. In a third terminal, start Ollama:
   ```bash
   ollama serve
   ```
2. Pull the default lightweight model:
   ```bash
   ollama pull qwen2.5:3b
   ```

---

## 🧪 Running Automated Tests

Run the backend unit and integration test suite:

```bash
cd project/backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

All 13 test scenarios verify:
- Query intent classification (Company detection, topic detection, policy routing)
- Company isolation (Network Marvels vs. IVP vs. Nomura)
- Abstention behavior on unsupported queries (anti-hallucination)
- All REST endpoints (`/api/health`, `/api/documents`, `/api/companies`, `/api/dashboard/*`, `/api/policy/sections`)

---

## 💡 Sample Test Queries

Try entering these in the **AI Assistant** or **RAG Explorer**:

| Query | Expected Grounded Behavior |
|---|---|
| *"What was the IVP online assessment pattern?"* | Returns the exact breakdown: 12 aptitude, 27 technical MCQs, 2 coding questions, citing IVP PDF (Pages 1–3). |
| *"What coding question was asked at Network Marvels?"* | Returns the documented string manipulation question without leaking IVP's coding problems. |
| *"What was the aptitude test pattern for Nomura?"* | Abstains / clarifies that Nomura had a hackathon-based evaluation (executive summary + presentation), not an aptitude test. |
| *"What was the internship stipend at ISS?"* | States that internship stipend is not documented in the available ISS Stoxx experiences. |
| *"Compare the selection processes of IVP and Network Marvels"* | Generates a structured side-by-side comparison with citations to both independent source documents. |
| *"What does VESIT policy state regarding placement eligibility?"* | Retrieves authoritative clauses from the official VESIT Internship Handbook. |

---

## 🔒 Privacy & Security

- **Local Storage**: All files, vector stores, and relational records reside on your local machine (`storage/`).
- **Path Traversal Protection**: Uploaded filenames are sanitized and validated against allowed extensions (`.pdf`, `.docx`, `.txt`, `.md`).
- **No Paid APIs**: Does not stream private student placement data or contact information to external third-party cloud services.
