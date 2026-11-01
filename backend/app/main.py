"""FastAPI application entry point."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, companies, dashboard, documents, health, policy, rag
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger
from app.database.base import SessionLocal
from app.database.init_db import init_db

logger = get_logger(__name__)


async def _startup_ingest():
    """Scan existing document directories and index any new files."""
    from app.services.ingestion.pipeline import IngestionPipeline

    db = SessionLocal()
    try:
        pipeline = IngestionPipeline(db=db)
        logger.info("Scanning placement_experience directory: %s", settings.PLACEMENT_EXPERIENCE_PATH)
        docs = pipeline.scan_and_ingest_directory(
            settings.PLACEMENT_EXPERIENCE_PATH, doc_type="placement_experience"
        )
        logger.info("Scanned placement_experience: %d documents processed", len(docs))

        logger.info("Scanning policy directory: %s", settings.POLICY_PATH)
        pol = pipeline.scan_and_ingest_directory(
            settings.POLICY_PATH, doc_type="policy"
        )
        logger.info("Scanned policy: %d documents processed", len(pol))
    except Exception as exc:
        logger.error("Startup ingestion error: %s", exc, exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB and scan documents on startup."""
    logger.info("Initialising database schema …")
    init_db()
    logger.info("Database ready.")

    # Create storage directories
    Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOADS_PATH).mkdir(parents=True, exist_ok=True)

    logger.info("Running startup document ingestion …")
    await asyncio.to_thread(_startup_ingest_sync)

    yield

    logger.info("Shutting down Placenta backend.")


def _startup_ingest_sync():
    """Synchronous wrapper for startup ingestion."""
    from app.services.ingestion.pipeline import IngestionPipeline

    db = SessionLocal()
    try:
        pipeline = IngestionPipeline(db=db)
        logger.info("Scanning %s …", settings.PLACEMENT_EXPERIENCE_PATH)
        docs = pipeline.scan_and_ingest_directory(
            settings.PLACEMENT_EXPERIENCE_PATH, doc_type="placement_experience"
        )
        logger.info("Placement experiences processed: %d", len(docs))

        logger.info("Scanning %s …", settings.POLICY_PATH)
        pol = pipeline.scan_and_ingest_directory(
            settings.POLICY_PATH, doc_type="policy"
        )
        logger.info("Policy documents processed: %d", len(pol))
    except Exception as exc:
        logger.error("Startup ingestion failed: %s", exc, exc_info=True)
    finally:
        db.close()


app = FastAPI(
    title="Placenta — VESIT Placement Intelligence API",
    description="RAG-powered placement experience and policy assistant for VESIT.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(rag.router, prefix="/api", tags=["rag"])
app.include_router(policy.router, prefix="/api", tags=["policy"])


@app.get("/")
def root():
    return {
        "name": "Placenta",
        "description": "VESIT Placement Experience & Policy Intelligence Platform",
        "docs": "/docs",
        "health": "/api/health",
    }

