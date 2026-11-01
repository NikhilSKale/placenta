"""Application configuration via Pydantic Settings."""
from __future__ import annotations

import json
import os
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:////Users/nick/Nick/Vesit/genai/storage/application.db"
    CHROMA_PATH: str = "/Users/nick/Nick/Vesit/genai/storage/chroma"
    UPLOADS_PATH: str = "/Users/nick/Nick/Vesit/genai/storage/uploads"

    # ── Document sources ──────────────────────────────────────────────────────
    PLACEMENT_EXPERIENCE_PATH: str = "/Users/nick/Nick/Vesit/genai/project/placement_experience"
    POLICY_PATH: str = "/Users/nick/Nick/Vesit/genai/project/vesit_policy"

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # ── LLM ───────────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT: int = 120

    # ── RAG settings ─────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_TOP_K: int = 8
    SIMILARITY_THRESHOLD: float = 0.3

    # ── Security ──────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: Union[List[str], str] = [".pdf", ".docx", ".txt", ".md"]

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_EXTENSIONS", "CORS_ORIGINS", mode="after")
    @classmethod
    def parse_to_list(cls, v):
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [ext.strip() for ext in v_str.split(",") if ext.strip()]
        return list(v)


settings = Settings()
