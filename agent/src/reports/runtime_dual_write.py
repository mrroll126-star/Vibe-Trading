"""Default-off runtime trace enrichment for financial tool results."""

from __future__ import annotations

import os
from typing import Any

from src.reports.financial_provenance import build_financial_provenance_enrichment
from src.reports.tool_dual_write import create_dual_write_tool_event


_FINANCIAL_TOOL = "get_financial_statements"


def is_structured_tool_trace_enabled() -> bool:
    """Return whether runtime structured trace enrichment is explicitly enabled."""

    return os.getenv("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", "").strip() == "1"


def build_financial_trace_enrichment(
    *,
    tool_name: str,
    redacted_result: str,
    tool_args: dict[str, Any] | None = None,
    execution_metadata: dict[str, Any] | None = None,
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
            args=dict(tool_args or {}),
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

    payload = event.get("structured_payload")
    if not isinstance(payload, dict):
        return {
            "trace_schema_version": event["trace_schema_version"],
            "tool_name": event["tool_name"],
            "structured_payload": payload,
            "human_summary": event["human_summary"],
            "metadata": event["metadata"],
            "structured_trace_warnings": event["structured_trace_warnings"],
        }

    try:
        projected = build_financial_provenance_enrichment(
            payload=payload,
            tool_name=tool_name,
            tool_args=dict(tool_args or {}),
            execution_metadata=dict(execution_metadata or {}),
            serializer_metadata=event.get("metadata") if isinstance(event.get("metadata"), dict) else None,
        )
    except Exception:  # noqa: BLE001 - provenance enrichment cannot block execution
        warnings = list(event.get("structured_trace_warnings") or [])
        if "financial_provenance_projection_failed" not in warnings:
            warnings.append("financial_provenance_projection_failed")
        return {
            "trace_schema_version": event["trace_schema_version"],
            "tool_name": event["tool_name"],
            "structured_payload": payload,
            "human_summary": event["human_summary"],
            "metadata": event["metadata"],
            "structured_trace_warnings": warnings,
        }

    return {
        "trace_schema_version": event["trace_schema_version"],
        "tool_name": event["tool_name"],
        "structured_payload": projected["structured_payload"],
        "human_summary": event["human_summary"],
        "metadata": projected["metadata"],
        # Projection is authoritative for provenance warnings. Serializer-only
        # metadata-missing warnings may be resolved by explicit runtime facts.
        "structured_trace_warnings": list(projected["warnings"]),
    }
