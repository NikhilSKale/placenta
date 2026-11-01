"""Observability, Telemetry, and MCP API endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag.guardrails import guardrails_service
from app.services.rag.mcp_server import mcp_tool_handler
from app.services.rag.observability import observability_service
from app.services.rag.semantic_cache import semantic_cache

router = APIRouter(prefix="/rag", tags=["RAG & Observability"])


class MCPToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


@router.get("/metrics")
def get_observability_metrics():
    """Retrieve live RAG observability metrics, faithfulness scores, and latency percentiles."""
    metrics = observability_service.get_metrics()
    cache_stats = semantic_cache.stats()
    return {
        "observability": metrics,
        "cache": cache_stats,
    }


@router.post("/cache/clear")
def clear_semantic_cache():
    """Clears the semantic vector cache."""
    semantic_cache.clear()
    return {"status": "cleared", "total_cached_queries": 0}


@router.get("/mcp/tools")
def list_mcp_tools():
    """Returns the registered MCP (Model Context Protocol) tools for placement data."""
    return {"tools": mcp_tool_handler.list_tools()}


@router.post("/mcp/call")
def call_mcp_tool(req: MCPToolCallRequest):
    """Executes an MCP tool call."""
    try:
        result = mcp_tool_handler.call_tool(req.tool_name, req.arguments)
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

