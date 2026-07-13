"""Fixture-first structured tool-result serializer.

This module converts already-produced tool envelopes into the trace-contract
shape without invoking tools, providers, AgentLoop, or an LLM.
"""

from __future__ import annotations

import json
from typing import Any


_SUPPORTED_TOOLS = {"get_market_data", "get_financial_statements"}
_METADATA_FIELDS = ("provider", "source", "upstream", "data_quality", "timestamps")


def serialize_tool_result(
    *,
    tool_name: str,
    raw_result: Any,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a trace-contract envelope from a structured tool result.

    ``raw_result`` is accepted only as an existing mapping or a complete JSON
    object string. Rendered legacy text is deliberately not parsed or inferred.
    """

    supplied_metadata = dict(metadata or {})
    warnings: list[str] = []
    if tool_name not in _SUPPORTED_TOOLS:
        return _unstructured_envelope(
            tool_name,
            supplied_metadata,
            ["unsupported_tool_for_structured_payload"],
        )

    payload = _decode_structured_payload(raw_result)
    if payload is None:
        return _unstructured_envelope(
            tool_name,
            supplied_metadata,
            ["legacy_unstructured_result"],
        )

    resolved_metadata = _resolve_metadata(payload, supplied_metadata)
    for field in ("provider", "source"):
        if not resolved_metadata.get(field):
            warnings.append(f"metadata_{field}_missing")
    if not resolved_metadata.get("data_quality"):
        warnings.append("metadata_data_quality_missing")

    ok = payload.get("ok")
    status = "ok" if ok is not False else "error"
    return {
        "tool_name": tool_name,
        "status": status,
        "structured_payload": payload,
        "human_summary": _human_summary(tool_name, supplied_metadata, structured=True),
        "metadata": resolved_metadata,
        "warnings": warnings,
    }


def _decode_structured_payload(raw_result: Any) -> dict[str, Any] | None:
    if isinstance(raw_result, dict):
        return dict(raw_result)
    if not isinstance(raw_result, str):
        return None
    try:
        parsed = json.loads(raw_result)
    except json.JSONDecodeError:
        return None
    return dict(parsed) if isinstance(parsed, dict) else None


def _resolve_metadata(payload: dict[str, Any], supplied: dict[str, Any]) -> dict[str, Any]:
    quality = supplied.get("data_quality")
    if not isinstance(quality, dict):
        candidate = payload.get("_data_quality")
        quality = dict(candidate) if isinstance(candidate, dict) else {}

    quality_entry = _first_quality_entry(quality)
    resolved: dict[str, Any] = {}
    for field in _METADATA_FIELDS:
        if field == "data_quality":
            resolved[field] = quality
            continue
        value = supplied.get(field)
        if value in (None, ""):
            value = payload.get(field)
        if value in (None, ""):
            value = quality_entry.get(field)
        resolved[field] = value if value is not None else ""
    return resolved


def _first_quality_entry(quality: dict[str, Any]) -> dict[str, Any]:
    for value in quality.values():
        if isinstance(value, dict):
            return value
    return {}


def _unstructured_envelope(
    tool_name: str,
    metadata: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "status": "error",
        "structured_payload": None,
        "human_summary": _human_summary(tool_name, metadata, structured=False),
        "metadata": {field: metadata.get(field, {} if field == "data_quality" else "") for field in _METADATA_FIELDS},
        "warnings": warnings,
    }


def _human_summary(tool_name: str, metadata: dict[str, Any], *, structured: bool) -> str:
    custom = metadata.get("human_summary")
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    if structured:
        return f"Structured result available for {tool_name}."
    return f"Structured result unavailable for {tool_name}; legacy text retained separately."
