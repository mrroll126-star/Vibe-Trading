"""Fixture-only research schema artifact envelope generator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.reports.report_builder import ReportBuildError
from src.reports.trace_collector import build_research_report_from_trace_events


SCHEMA_VERSION = "1.0"
GENERATOR_VERSION = "1.0"


def generate_research_artifact(
    *,
    run_id: str,
    trace_events: list[dict[str, Any]] | None,
    input_symbol: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable artifact envelope from in-memory trace fixtures.

    This function intentionally does not read traces from disk or write an
    artifact file. It is the fixture-only proof of the post-processing contract.
    """

    metadata = metadata or {}
    generated_at = str(metadata.get("generated_at") or datetime.now(UTC).isoformat(timespec="seconds"))
    generator_version = str(metadata.get("generator_version") or GENERATOR_VERSION)
    if not isinstance(trace_events, list) or not trace_events:
        return _failed_artifact(
            run_id=run_id,
            generated_at=generated_at,
            generator_version=generator_version,
            error="trace_events_missing_or_empty",
        )

    try:
        report = build_research_report_from_trace_events(
            trace_events,
            input_symbol=input_symbol,
            run_id=run_id,
            generated_at=generated_at,
            provider=str(metadata.get("provider") or ""),
            model=str(metadata.get("model") or ""),
        )
    except (ReportBuildError, TypeError, ValueError):
        return _failed_artifact(
            run_id=run_id,
            generated_at=generated_at,
            generator_version=generator_version,
            error="research_report_build_failed",
            event_count=len(trace_events),
        )

    status = _artifact_status(report)
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_meta": {
            "run_id": run_id,
            "generated_at": generated_at,
            "status": status,
            "generator_version": generator_version,
            "trace_event_count": len(trace_events),
        },
        "research_report": report,
        "errors": [],
    }


def _artifact_status(report: dict[str, Any]) -> str:
    market_status = str(report.get("market_snapshot", {}).get("status") or "")
    financial_status = str(report.get("financial_health", {}).get("status") or "")
    warnings = report.get("data_confidence", {}).get("warnings")
    warning_set = {str(item) for item in warnings} if isinstance(warnings, list) else set()
    if market_status == "available" and financial_status == "complete" and "final_answer_missing_from_trace" not in warning_set:
        return "complete"
    return "partial"


def _failed_artifact(
    *,
    run_id: str,
    generated_at: str,
    generator_version: str,
    error: str,
    event_count: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_meta": {
            "run_id": run_id,
            "generated_at": generated_at,
            "status": "failed",
            "generator_version": generator_version,
            "trace_event_count": event_count,
        },
        "research_report": {},
        "errors": [error],
    }
