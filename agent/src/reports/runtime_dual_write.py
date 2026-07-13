"""Default-off runtime trace enrichment for financial tool results."""

from __future__ import annotations

import os
from typing import Any

from src.reports.tool_dual_write import create_dual_write_tool_event


_FINANCIAL_TOOL = "get_financial_statements"


def is_structured_tool_trace_enabled() -> bool:
    """Return whether runtime structured trace enrichment is explicitly enabled."""

    return os.getenv("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", "").strip() == "1"


def build_financial_trace_enrichment(
    *,
    tool_name: str,
    redacted_result: str,
) -> dict[str, Any] | None:
    """Build best-effort trace-only enrichment for the financial tool.

    This function never changes the legacy result and must never raise into
    tool execution. Only the feature-flagged financial tool is allowlisted.
    """

    if not is_structured_tool_trace_enabled() or tool_name != _FINANCIAL_TOOL:
        return None
    try:
        event = create_dual_write_tool_event(
            tool_name=tool_name,
            args={},
            raw_result=redacted_result,
        )
    except Exception:  # noqa: BLE001 - audit enrichment cannot block execution
        return {
            "trace_schema_version": "tool_result.v1",
            "tool_name": tool_name,
            "structured_payload": None,
            "human_summary": f"Structured result unavailable for {tool_name}.",
            "metadata": {},
            "structured_trace_warnings": ["structured_payload_unavailable"],
        }

    return {
        "trace_schema_version": event["trace_schema_version"],
        "tool_name": event["tool_name"],
        "structured_payload": event["structured_payload"],
        "human_summary": event["human_summary"],
        "metadata": event["metadata"],
        "structured_trace_warnings": event["structured_trace_warnings"],
    }
