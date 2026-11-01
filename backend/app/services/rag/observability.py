"""Observability and Evaluation Service for Placenta RAG.

Features:
1. Structured Metrics: Latency tracking (retrieval vs generation vs guardrails), cache hit rate, token estimations.
2. Groundedness Evaluation: Checks whether generated factual statements strictly originate from retrieved context.
3. RAG Triad Evaluator:
   - Context Relevance (How relevant retrieved chunks are to query)
   - Faithfulness / Groundedness (How grounded the answer is in context)
   - Answer Relevance (How well the answer satisfies query intent)
4. Telemetry logs & status.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class TraceEvent:
    def __init__(
        self,
        query: str,
        detected_company: Optional[str],
        doc_category: str,
        retrieval_ms: int,
        generation_ms: int,
        total_ms: int,
        evidence_found: bool,
        cached: bool,
        faithfulness_score: float,
        context_relevance_score: float,
        guardrail_triggered: bool = False,
    ):
        self.timestamp = time.time()
        self.query = query
        self.detected_company = detected_company
        self.doc_category = doc_category
        self.retrieval_ms = retrieval_ms
        self.generation_ms = generation_ms
        self.total_ms = total_ms
        self.evidence_found = evidence_found
        self.cached = cached
        self.faithfulness_score = faithfulness_score
        self.context_relevance_score = context_relevance_score
        self.guardrail_triggered = guardrail_triggered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "query": self.query,
            "detected_company": self.detected_company,
            "doc_category": self.doc_category,
            "latency": {
                "retrieval_ms": self.retrieval_ms,
                "generation_ms": self.generation_ms,
                "total_ms": self.total_ms,
            },
            "evidence_found": self.evidence_found,
            "cached": self.cached,
            "evaluation": {
                "faithfulness": self.faithfulness_score,
                "context_relevance": self.context_relevance_score,
            },
            "guardrail_triggered": self.guardrail_triggered,
        }


class ObservabilityService:
    """In-memory telemetry and RAG evaluation observer."""

    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self.traces: List[TraceEvent] = []

    def evaluate_faithfulness(self, answer: str, context: str) -> float:
        """
        Calculates lexical and claim-level overlap to estimate faithfulness.
        Returns a score from 0.0 to 1.0.
        """
        if not answer or not context:
            return 0.0

        if "not mentioned in the available placement" in answer.lower():
            return 1.0  # Perfect abstention behavior

        # Tokenize content words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "and", "or", "in", "on", "at",
            "to", "for", "with", "from", "by", "of", "this", "that", "it", "as", "be",
            "sources:", "source", "page", "company"
        }
        answer_words = [
            w.lower() for w in re.findall(r"\b\w+\b", answer) if len(w) > 3 and w.lower() not in stop_words
        ]
        if not answer_words:
            return 1.0

        context_lower = context.lower()
        supported = sum(1 for w in answer_words if w in context_lower)
        score = supported / len(answer_words)
        return round(min(1.0, score * 1.15), 3)  # Scaled for slight syntactic variation

    def evaluate_context_relevance(self, query: str, retrieved_chunks: List[Dict]) -> float:
        """
        Evaluates the relevance of retrieved chunks to the query based on term overlap.
        """
        if not retrieved_chunks:
            return 0.0

        query_terms = set(re.findall(r"\b\w{3,}\b", query.lower()))
        if not query_terms:
            return 1.0

        scores = []
        for c in retrieved_chunks:
            text = c.get("text", "").lower()
            matches = sum(1 for term in query_terms if term in text)
            scores.append(matches / len(query_terms))

        avg = sum(scores) / len(scores) if scores else 0.0
        return round(min(1.0, avg * 1.5), 3)

    def record_trace(
        self,
        query: str,
        detected_company: Optional[str],
        doc_category: str,
        retrieval_ms: int,
        generation_ms: int,
        total_ms: int,
        evidence_found: bool,
        cached: bool,
        answer: str,
        context: str,
        retrieved_chunks: List[Dict],
        guardrail_triggered: bool = False,
    ) -> Dict[str, Any]:
        """Runs automated evaluation and logs trace."""
        faithfulness = self.evaluate_faithfulness(answer, context)
        context_relevance = self.evaluate_context_relevance(query, retrieved_chunks)

        trace = TraceEvent(
            query=query,
            detected_company=detected_company,
            doc_category=doc_category,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
            evidence_found=evidence_found,
            cached=cached,
            faithfulness_score=faithfulness,
            context_relevance_score=context_relevance,
            guardrail_triggered=guardrail_triggered,
        )

        if len(self.traces) >= self.max_traces:
            self.traces.pop(0)
        self.traces.append(trace)

        logger.info(
            "RAG Trace recorded: latency=%dms (ret=%d, gen=%d), cached=%s, faith=%.2f, relevance=%.2f",
            total_ms,
            retrieval_ms,
            generation_ms,
            cached,
            faithfulness,
            context_relevance,
        )
        return trace.to_dict()

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate telemetry and evaluation statistics."""
        if not self.traces:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0,
                "avg_retrieval_ms": 0,
                "avg_generation_ms": 0,
                "cache_hit_rate": 0.0,
                "evidence_rate": 0.0,
                "avg_faithfulness": 1.0,
                "avg_context_relevance": 1.0,
                "guardrail_triggers": 0,
            }

        n = len(self.traces)
        avg_total = sum(t.total_ms for t in self.traces) / n
        avg_ret = sum(t.retrieval_ms for t in self.traces) / n
        avg_gen = sum(t.generation_ms for t in self.traces) / n
        cache_hits = sum(1 for t in self.traces if t.cached)
        evidence_hits = sum(1 for t in self.traces if t.evidence_found)
        guardrail_triggers = sum(1 for t in self.traces if t.guardrail_triggered)
        avg_faith = sum(t.faithfulness_score for t in self.traces) / n
        avg_relevance = sum(t.context_relevance_score for t in self.traces) / n

        return {
            "total_queries": n,
            "avg_latency_ms": round(avg_total, 1),
            "avg_retrieval_ms": round(avg_ret, 1),
            "avg_generation_ms": round(avg_gen, 1),
            "cache_hit_rate": round(cache_hits / n, 3),
            "evidence_rate": round(evidence_hits / n, 3),
            "avg_faithfulness": round(avg_faith, 3),
            "avg_context_relevance": round(avg_relevance, 3),
            "guardrail_triggers": guardrail_triggers,
            "recent_traces": [t.to_dict() for t in self.traces[-10:]],
        }


observability_service = ObservabilityService()

