"""Integration and behavioral tests for Placenta RAG Engine and anti-hallucination rules."""
from __future__ import annotations

import pytest
from app.services.rag.query_classifier import classify_query
from app.services.rag.rag_engine import RAGEngine, NO_CONTEXT_RESPONSE


def test_query_classification_company():
    q = "What was the IVP online assessment pattern?"
    analysis = classify_query(q)
    assert analysis.detected_company == "IVP"
    assert "Aptitude" in analysis.detected_topics or "Coding" in analysis.detected_topics


def test_query_classification_network_marvels():
    q = "What coding question was asked at Network Marvels?"
    analysis = classify_query(q)
    assert analysis.detected_company == "Network Marvels"
    assert "Coding" in analysis.detected_topics


def test_query_classification_nomura_hackathon():
    q = "What was the aptitude test pattern for Nomura?"
    analysis = classify_query(q)
    assert analysis.detected_company == "Nomura"


def test_query_classification_policy():
    q = "According to VESIT's official placement policy, what restrictions apply?"
    analysis = classify_query(q)
    assert analysis.doc_category == "policy"
    assert analysis.intent == "policy"


def test_query_classification_comparison():
    q = "Compare the selection processes of IVP and Network Marvels"
    analysis = classify_query(q)
    assert analysis.is_comparison is True
    assert analysis.intent == "comparison"


def test_unsupported_fact_no_hallucination():
    engine = RAGEngine()
    # A company not in any documents
    result = engine.answer(query="What was the CTC offered by Google Mountain View campus?")
    assert result is not None
    # Either evidence not found or abstained
    if not result.get("evidence_found"):
        assert "unable to find" in result["answer"].lower() or "not mentioned" in result["answer"].lower()

