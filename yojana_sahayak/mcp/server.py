"""
Yojana Sahayak MCP Server
==========================

Exposes Indian government scheme data as MCP (Model Context Protocol) tools.
Designed for integration with agentic AI systems — including air-gapped,
on-premise deployments where LLMs invoke tools via stdio transport.

Tools:
    - search_schemes: Semantic search over 591+ scheme facts
    - get_scheme_details: Retrieve specific scheme info by name and field
    - check_eligibility: Check eligibility for a named scheme
    - list_schemes: List all indexed schemes

Transport:
    - stdio (default): Zero network dependency. MCP server runs as a child
      process communicating via piped JSON-RPC. Ideal for air-gapped environments.
    - SSE: For web-based integrations.

Usage:
    # stdio mode (for air-gapped / on-prem deployment)
    python -m yojana_sahayak.mcp.server

    # Or via the CLI entry point
    yojana-mcp
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Lazy imports to keep startup fast
_retriever = None


def _get_retriever():
    """Lazy-initialize the scheme retriever."""
    global _retriever
    if _retriever is None:
        from yojana_sahayak.rag.retriever import SchemeRetriever
        _retriever = SchemeRetriever()
        _retriever.build_index()
    return _retriever


def _load_core_schemes() -> dict:
    """Load core scheme metadata for direct lookup."""
    core_path = Path(__file__).parent.parent.parent / "data" / "core_schemes.jsonl"
    schemes = {}
    if core_path.exists():
        with open(core_path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                name = rec.get("scheme_name", "")
                if name not in schemes:
                    schemes[name] = {}
                field = rec.get("field", "")
                msgs = rec.get("messages", [])
                answer = next(
                    (m["content"] for m in msgs if m["role"] == "assistant"), ""
                )
                if field and answer:
                    schemes[name][field] = answer
    return schemes


# ── MCP Tool Implementations ─────────────────────────────────────────────────

def search_schemes(query: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search over Indian government scheme facts.

    Args:
        query: Natural language query in Hindi or English.
               Examples: 'PM Kisan ke liye kaun eligible hai?',
                         'What are the benefits of Ayushman Bharat?'
        top_k: Number of results to return (default 3).

    Returns:
        List of matching scheme facts with scheme name, field, answer, and relevance score.
    """
    retriever = _get_retriever()
    return retriever.retrieve(query, top_k=top_k)


def get_scheme_details(scheme_name: str,
                       field: Optional[str] = None) -> dict:
    """
    Get details about a specific government scheme.

    Args:
        scheme_name: Name of the scheme (e.g., 'PM Kisan', 'Ayushman Bharat').
        field: Specific field to retrieve. One of:
               'eligibility', 'benefits', 'description', 'application_process'.
               If None, returns all available fields.

    Returns:
        Dict with scheme info. Keys are field names, values are descriptions.
    """
    schemes = _load_core_schemes()

    # Fuzzy match on scheme name
    name_lower = scheme_name.lower()
    matched = None
    for name in schemes:
        if name_lower in name.lower() or name.lower() in name_lower:
            matched = name
            break

    if not matched:
        # Fall back to semantic search
        results = search_schemes(scheme_name, top_k=1)
        if results:
            return {
                "scheme": results[0]["scheme"],
                "field": results[0]["field"],
                "info": results[0]["answer"],
                "source": "semantic_search",
            }
        return {"error": f"No information found for '{scheme_name}'"}

    info = schemes[matched]
    if field and field in info:
        return {"scheme": matched, "field": field, "info": info[field]}
    return {"scheme": matched, "fields": info}


def check_eligibility(scheme_name: str, user_context: str = "") -> dict:
    """
    Check eligibility criteria for a government scheme.

    Args:
        scheme_name: Name of the scheme to check.
        user_context: Optional user details for personalized matching
                      (e.g., 'farmer with 1 hectare land in UP').

    Returns:
        Dict with eligibility criteria and match assessment.
    """
    query = f"{scheme_name} eligibility {user_context}".strip()
    results = search_schemes(query, top_k=2)

    eligibility_results = [r for r in results if r["field"] == "eligibility"]
    if not eligibility_results:
        eligibility_results = results

    if not eligibility_results:
        return {"error": f"No eligibility information found for '{scheme_name}'"}

    return {
        "scheme": eligibility_results[0]["scheme"],
        "eligibility_criteria": eligibility_results[0]["answer"],
        "confidence": eligibility_results[0]["score"],
    }


def list_schemes() -> dict:
    """
    List all government schemes in the knowledge base.

    Returns:
        Dict with 'count' and 'schemes' (list of unique scheme names).
    """
    retriever = _get_retriever()
    if not retriever._docs:
        return {"count": 0, "schemes": []}

    names = sorted(set(d["scheme"] for d in retriever._docs))
    return {"count": len(names), "schemes": names}


# ── MCP Server (FastMCP) ─────────────────────────────────────────────────────

def create_mcp_server():
    """Create and configure the MCP server with all tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("Install MCP SDK: pip install 'mcp[cli]'", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP(
        "yojana-sahayak",
        instructions=(
            "Indian Government Scheme Assistant — search, retrieve, and check "
            "eligibility for 2,872+ central and state government welfare schemes. "
            "Supports Hindi and English queries."
        ),
    )

    @mcp.tool()
    def tool_search_schemes(query: str, top_k: int = 3) -> str:
        """Search government schemes by natural language query (Hindi or English)."""
        results = search_schemes(query, top_k)
        return json.dumps(results, ensure_ascii=False, indent=2)

    @mcp.tool()
    def tool_get_scheme(scheme_name: str, field: str = "") -> str:
        """Get details about a specific scheme. Fields: eligibility, benefits, description, application_process."""
        result = get_scheme_details(scheme_name, field or None)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool()
    def tool_check_eligibility(scheme_name: str, user_context: str = "") -> str:
        """Check if someone is eligible for a scheme. Optionally provide user details for matching."""
        result = check_eligibility(scheme_name, user_context)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool()
    def tool_list_schemes() -> str:
        """List all government schemes in the knowledge base."""
        result = list_schemes()
        return json.dumps(result, ensure_ascii=False, indent=2)

    return mcp


def main():
    """Run the MCP server (stdio transport by default)."""
    server = create_mcp_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
