"""Fixture-first helper for legacy-plus-structured trace result events."""

from __future__ import annotations

import json
from typing import Any

from src.reports.tool_result_serializer import serialize_tool_result


def create_dual_write_tool_event(
    *,
    tool_name: str,
    args: dict[str, Any],
    raw_result: Any,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a trace-compatible dual-write event without executing a tool.

    The legacy text is always retained. Serializer failures are converted into
    trace-only warnings and never raise into the caller.
    """

    legacy_result = _legacy_result_text(raw_result)
    try:
        serialized = serialize_tool_result(
            tool_name=tool_name,
            raw_result=raw_result,
            metadata=metadata,
        )
    except Exception:  # noqa: BLE001 - trace enrichment is best effort
        serialized = {
            "status": _legacy_status(raw_result),
            "structured_payload": None,
            "human_summary": f"Structured result unavailable for {tool_name}.",
            "metadata": dict(metadata or {}),
            "warnings": ["structured_payload_unavailable"],
        }

    warnings = list(serialized.get("warnings") or [])
    if serialized.get("structured_payload") is None and "structured_payload_unavailable" not in warnings:
        warnings.append("structured_payload_unavailable")

    return {
        "type": "tool_result",
        "trace_schema_version": "tool_result.v1",
        "tool": tool_name,
        "tool_name": tool_name,
        "args": dict(args),
        "status": str(serialized.get("status") or _legacy_status(raw_result)),
        "result": legacy_result,
        "structured_payload": serialized.get("structured_payload"),
        "human_summary": str(serialized.get("human_summary") or ""),
        "metadata": dict(serialized.get("metadata") or {}),
        "structured_trace_warnings": warnings,
    }


def _legacy_result_text(raw_result: Any) -> str:
    if isinstance(raw_result, str):
        return raw_result
    return json.dumps(raw_result, ensure_ascii=False, sort_keys=True)


def _legacy_status(raw_result: Any) -> str:
    payload: Any = raw_result
    if isinstance(raw_result, str):
        try:
            payload = json.loads(raw_result)
        except json.JSONDecodeError:
            return "ok"
    return "error" if isinstance(payload, dict) and payload.get("ok") is False else "ok"
