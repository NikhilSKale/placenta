"""Query routing and retrieval strategy dispatcher."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.rag.query_classifier import QueryAnalysis, classify_query


def route_query(
    query: str,
    override_company: Optional[str] = None,
    override_doc_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes intent, topic, and entity to route to the optimal
    vector collection and apply optimal filtering/retrieval parameters.
    """
    analysis = classify_query(query)

    if override_company:
        analysis.detected_company = override_company
        analysis.chroma_where = {"company": {"$eq": override_company}}

    if override_doc_type and override_doc_type != "all":
        analysis.doc_category = override_doc_type

    # Select target collection based on doc category
    if analysis.doc_category == "policy":
        collection = "policy_documents"
    else:
        collection = "placement_experiences"

    # Dynamic top_k based on query breadth
    if analysis.intent in ("compare", "summary"):
        suggested_top_k = 12
    elif analysis.intent == "specific_fact":
        suggested_top_k = 6
    else:
        suggested_top_k = 8

    return {
        "analysis": analysis,
        "collection": collection,
        "chroma_where": analysis.chroma_where,
        "suggested_top_k": suggested_top_k,
    }

