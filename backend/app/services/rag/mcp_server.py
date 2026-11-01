"""FastMCP / Model Context Protocol (MCP) server for Placenta VESIT Placement Assistant.

Provides LLMs and external agent platforms with tool-calling capabilities to:
1. search_placement_experiences: Query student interview questions, selection rounds, and packages.
2. query_placement_policy: Check official VESIT CGPA criteria, dream-company rules, backlogs, etc.
3. get_company_stats: Retrieve structured placement metrics for a company.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.database.base import SessionLocal
from app.models.models import Document, ExtractedFact, PlacementExperience
from app.services.rag.rag_engine import RAGEngine


class PlacentaMCPToolHandler:
    """Implements standard MCP tool execution for RAG & Placement data."""

    def __init__(self):
        self.rag_engine = RAGEngine()

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_placement_experiences",
                "description": (
                    "Search through VESIT student placement experiences. "
                    "Use this to find interview questions, technical rounds, coding questions, "
                    "tips, and package/CTC information for companies."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The student question or query"},
                        "company": {"type": "string", "description": "Optional company name to filter by (e.g. 'IVP', 'TCS', 'Nomura')"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "query_placement_policy",
                "description": (
                    "Query the official VESIT placement policy document. "
                    "Answers rules regarding eligibility, multiple offers, dream status, CGPA cutoffs, and attendance requirements."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Specific placement rule or question"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_company_stats",
                "description": "Fetch extracted facts and statistics for a specific recruited company at VESIT.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "Company name (e.g., 'IVP', 'Nomura', 'TCS')"},
                    },
                    "required": ["company_name"],
                },
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_placement_experiences":
            query = arguments.get("query", "")
            company = arguments.get("company")
            res = self.rag_engine.answer(query=query, filter_company=company, filter_doc_type="placement_experience")
            return {
                "answer": res["answer"],
                "evidence_found": res.get("evidence_found", False),
                "sources": res.get("sources", []),
            }

        elif name == "query_placement_policy":
            query = arguments.get("query", "")
            res = self.rag_engine.answer(query=query, filter_doc_type="policy")
            return {
                "answer": res["answer"],
                "evidence_found": res.get("evidence_found", False),
                "sources": res.get("sources", []),
            }

        elif name == "get_company_stats":
            company_name = arguments.get("company_name", "").strip()
            db = SessionLocal()
            try:
                exp = db.query(PlacementExperience).filter(PlacementExperience.company_name.ilike(f"%{company_name}%")).first()
                if not exp:
                    return {"found": False, "message": f"Company '{company_name}' not found in database."}

                facts = db.query(ExtractedFact).filter(ExtractedFact.document_id == exp.document_id).all()
                return {
                    "found": True,
                    "company": exp.company_name,
                    "role": exp.job_role,
                    "fixed_ctc": exp.fixed_ctc,
                    "total_ctc": exp.total_ctc,
                    "stipend": exp.internship_stipend,
                    "facts": [
                        {
                            "category": f.category,
                            "key": f.fact_key,
                            "value": f.fact_value,
                            "page": f.page_number,
                        }
                        for f in facts
                    ],
                }
            finally:
                db.close()

        else:
            raise ValueError(f"Unknown tool name: {name}")


mcp_tool_handler = PlacentaMCPToolHandler()
