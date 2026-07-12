"""Offline Agent trace fixture collector for research report schema proofs.

This module is intentionally pure. It does not read ``agent/.env``, call
providers, run AgentLoop, or depend on Web UI state. It converts already-loaded
trace-like events into the inputs expected by ``build_research_report``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.reports.report_builder import build_research_report


@dataclass
class TraceCollection:
    """Normalized tool result collection extracted from trace events."""

    input_symbol: str
    market_result: dict[str, Any] | None = None
    financial_results: list[dict[str, Any]] = field(default_factory=list)
    interpretation: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    generated_at: str | None = None
    provider: str = ""
    model: str = ""
    collection_warnings: list[str] = field(default_factory=list)
    raw_event_count: int = 0


def collect_tool_results_from_trace_events(
    events: list[dict[str, Any]],
    *,
    input_symbol: str,
    run_id: str = "",
    generated_at: str | None = None,
    provider: str = "",
    model: str = "",
) -> TraceCollection:
    """Collect report-builder inputs from controlled trace events.

    Supports both the current ``TraceWriter`` shape (``type``, ``tool``,
    ``result``) and the design-fixture shape (``event_type``, ``tool_name``,
    ``result``). Unknown events are ignored and recorded as collection warnings.
    """

    collection = TraceCollection(
        input_symbol=input_symbol,
        run_id=run_id,
        generated_at=generated_at,
        provider=provider,
        model=model,
        raw_event_count=len(events),
    )

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            collection.collection_warnings.append(f"event_{index}_ignored_non_dict")
            continue

        event_type = _event_type(event)
        if event_type == "tool_result":
            _collect_tool_result(collection, event, index)
        elif event_type in {"answer", "final_answer"}:
            _collect_final_answer(collection, event, index)
        elif event_type in {"tool_call", "start", "end", "message"}:
            continue
        else:
            collection.collection_warnings.append(f"event_{index}_ignored_unknown_type_{event_type or 'missing'}")

    if collection.market_result is None:
        collection.collection_warnings.append("market_data_missing")
        collection.collection_warnings.append("market_data_missing_from_trace")
    if not collection.financial_results:
        collection.collection_warnings.append("financial_data_missing")
        collection.collection_warnings.append("financial_data_missing_from_trace")
    if not collection.interpretation:
        collection.interpretation = _placeholder_interpretation("final_answer_missing")
        collection.collection_warnings.append("final_answer_missing_from_trace")

    return collection


def build_research_report_from_trace_events(
    events: list[dict[str, Any]],
    *,
    input_symbol: str,
    run_id: str = "",
    generated_at: str | None = None,
    provider: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Build a research report schema directly from controlled trace events."""

    collection = collect_tool_results_from_trace_events(
        events,
        input_symbol=input_symbol,
        run_id=run_id,
        generated_at=generated_at,
        provider=provider,
        model=model,
    )
    report = build_research_report(
        input_symbol=collection.input_symbol,
        market_result=collection.market_result,
        financial_results=collection.financial_results,
        interpretation=collection.interpretation,
        run_id=collection.run_id,
        generated_at=collection.generated_at,
        provider=collection.provider,
        model=collection.model,
    )
    _append_collection_warnings(report, collection.collection_warnings)
    report["research_meta"]["raw_event_count"] = collection.raw_event_count
    return report


def _collect_tool_result(collection: TraceCollection, event: dict[str, Any], index: int) -> None:
    tool_name = str(event.get("tool_name") or event.get("tool") or "")
    result = _decode_result(event.get("result"))
    status = str(event.get("status") or "").lower()

    if result is None:
        result = {
            "ok": False,
            "error": f"{tool_name or 'unknown_tool'}_result_missing_or_invalid",
            "data": [],
        }

    if status and status not in {"ok", "success"}:
        _add_result_warning(result, f"{tool_name or 'unknown_tool'}_status_{status}")

    if tool_name == "get_market_data":
        collection.market_result = result
    elif tool_name == "get_financial_statements":
        collection.financial_results.append(result)
    elif tool_name:
        collection.collection_warnings.append(f"event_{index}_tool_{tool_name}_ignored_for_schema")
    else:
        collection.collection_warnings.append(f"event_{index}_tool_result_missing_tool_name")


def _collect_final_answer(collection: TraceCollection, event: dict[str, Any], index: int) -> None:
    content = str(event.get("content") or event.get("answer") or "")
    if not content:
        collection.collection_warnings.append(f"event_{index}_final_answer_empty")
        return
    collection.interpretation = _placeholder_interpretation(content)


def _event_type(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("type") or "")


def _decode_result(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return dict(parsed) if isinstance(parsed, dict) else None
    return None


def _add_result_warning(result: dict[str, Any], warning: str) -> None:
    warnings = result.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
    if warning not in warnings:
        warnings.append(warning)
    result["warnings"] = warnings


def _placeholder_interpretation(source_text: str) -> dict[str, Any]:
    """Create schema-safe interpretation placeholders without inventing facts."""

    if source_text == "final_answer_missing":
        return {
            "thesis": "",
            "bull_case": [],
            "bear_case": [],
            "key_risks": [],
            "monitor_items": [],
            "business_risks": [],
            "financial_risks": [],
            "market_risks": [],
        }
    return {
        "thesis": source_text,
        "bull_case": [],
        "bear_case": [],
        "key_risks": [],
        "monitor_items": [],
        "business_risks": [],
        "financial_risks": [],
        "market_risks": [],
    }


def _append_collection_warnings(report: dict[str, Any], warnings: list[str]) -> None:
    if not warnings:
        return
    data_confidence = report.setdefault("data_confidence", {})
    existing = data_confidence.get("warnings")
    if not isinstance(existing, list):
        existing = []
    for warning in warnings:
        if warning not in existing:
            existing.append(warning)
    data_confidence["warnings"] = existing
