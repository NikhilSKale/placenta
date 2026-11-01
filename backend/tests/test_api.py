"""Unit tests for FastAPI endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "embedding_model" in data
    assert "vector_store_healthy" in data


def test_documents_endpoint():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_companies_endpoint():
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_dashboard_overview():
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_documents" in data
    assert "companies" in data


def test_dashboard_analytics():
    resp = client.get("/api/dashboard/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "ctc_by_company" in data
    assert "round_distribution" in data
    assert "topic_frequency" in data


def test_rag_status():
    resp = client.get("/api/rag/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "embedding_model" in data


def test_policy_sections():
    resp = client.get("/api/policy/sections")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data

