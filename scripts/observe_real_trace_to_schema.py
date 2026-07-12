#!/usr/bin/env python3
"""Observe an existing Agent trace and summarize schema compatibility.

This script is read-only with respect to Agent artifacts. It does not run
AgentLoop, call providers, read ``agent/.env``, or write production artifacts.
Optional JSON output is intended for ignored ``local_reports``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from src.agent.trace import TraceWriter  # noqa: E402
from src.reports import ReportBuildError, build_research_report_from_trace_events  # noqa: E402


REQUIRED_SCHEMA_SECTIONS = [
    "research_meta",
    "symbol",
    "market_snapshot",
    "financial_health",
    "investment_memo",
    "valuation",
    "risks",
    "data_confidence",
    "limitations",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read an existing Agent trace and produce a compact schema observation summary."
    )
    parser.add_argument("--run-id", default="", help="Run id under agent/runs.")
    parser.add_argument("--session-id", default="", help="Session id under agent/sessions.")
    parser.add_argument("--trace-path", default="", help="Path to trace.jsonl or its parent trace directory.")
    parser.add_argument("--symbol", default="", help="Explicit confirmed symbol, e.g. 600519.SH.")
    parser.add_argument("--output-dir", default="local_reports", help="Ignored output directory. Default: local_reports.")
    parser.add_argument("--limit-events", type=int, default=5000, help="Maximum events to inspect. Default: 5000.")
    return parser.parse_args()


def resolve_trace_source(
    *,
    trace_path: str = "",
    run_id: str = "",
    session_id: str = "",
    root: Path = ROOT,
) -> tuple[Path | None, dict[str, str]]:
    """Resolve a user-specified trace source without guessing."""

    meta = {"trace_source": "", "run_id": run_id, "session_id": session_id}
    if trace_path:
        path = Path(trace_path).expanduser()
        if not path.is_absolute():
            path = (root / path).resolve()
        trace_dir = path.parent if path.name == "trace.jsonl" else path
        meta["trace_source"] = str(trace_dir)
        return trace_dir, meta

    if run_id:
        trace_dir = root / "agent" / "runs" / run_id
        meta["trace_source"] = str(trace_dir)
        return trace_dir, meta

    if session_id:
        trace_dir = root / "agent" / "sessions" / session_id
        meta["trace_source"] = str(trace_dir)
        return trace_dir, meta

    return None, meta


def observe_trace_to_schema(
    *,
    trace_dir: Path | None,
    symbol: str = "",
    run_id: str = "",
    session_id: str = "",
    limit_events: int = 5000,
) -> dict[str, Any]:
    """Build a compact observation summary from an existing trace directory."""

    summary: dict[str, Any] = {
        "trace_source": str(trace_dir) if trace_dir else "",
        "run_id": run_id,
        "session_id": session_id,
        "event_count": 0,
        "tool_result_count": 0,
        "tool_names": [],
        "has_market_data": False,
        "financial_statement_types_found": [],
        "has_final_answer": False,
        "collector_warnings": [],
        "schema_generated": False,
        "schema_sections_present": [],
        "missing_sections": list(REQUIRED_SCHEMA_SECTIONS),
        "data_confidence_summary": {},
        "compatibility": {
            "can_read_trace": False,
            "has_tool_results": False,
            "has_required_financial_results": False,
            "can_build_schema": False,
            "suitable_for_future_artifact": False,
        },
    }

    if trace_dir is None:
        summary["error"] = "trace source required: provide --trace-path, --run-id, or --session-id"
        return summary

    trace_file = trace_dir / "trace.jsonl"
    if not trace_file.exists():
        summary["error"] = f"trace.jsonl not found: {trace_file}"
        return summary

    events = TraceWriter.read(trace_dir, resolve_offloads=True, resolve_fields={"result", "content", "prompt"})
    if limit_events > 0:
        events = events[:limit_events]
    summary["event_count"] = len(events)
    summary["compatibility"]["can_read_trace"] = True

    tool_results = [event for event in events if _event_type(event) == "tool_result"]
    summary["tool_result_count"] = len(tool_results)
    summary["tool_names"] = sorted({_tool_name(event) for event in tool_results if _tool_name(event)})
    summary["compatibility"]["has_tool_results"] = bool(tool_results)
    summary["has_market_data"] = "get_market_data" in summary["tool_names"]
    summary["has_final_answer"] = any(_event_type(event) in {"answer", "final_answer"} for event in events)
    statement_types = _financial_statement_types(tool_results)
    summary["financial_statement_types_found"] = statement_types
    summary["compatibility"]["has_required_financial_results"] = {"income", "balance", "cashflow"}.issubset(
        set(statement_types)
    )

    if not tool_results:
        summary["collector_warnings"].append("tool_results_missing_from_trace")
        return summary
    if not symbol:
        summary["collector_warnings"].append("explicit_symbol_required_for_schema_build")
        return summary

    try:
        report = build_research_report_from_trace_events(
            events,
            input_symbol=symbol,
            run_id=run_id,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    except ReportBuildError as exc:
        summary["error"] = str(exc)
        summary["collector_warnings"].append("schema_build_rejected")
        return summary

    present = [section for section in REQUIRED_SCHEMA_SECTIONS if section in report]
    missing = [section for section in REQUIRED_SCHEMA_SECTIONS if section not in report]
    summary["schema_generated"] = True
    summary["schema_sections_present"] = present
    summary["missing_sections"] = missing
    confidence = report.get("data_confidence") if isinstance(report.get("data_confidence"), dict) else {}
    summary["data_confidence_summary"] = _compact_data_confidence(confidence)
    summary["collector_warnings"] = list(confidence.get("warnings") or [])
    summary["compatibility"]["can_build_schema"] = True
    summary["compatibility"]["suitable_for_future_artifact"] = (
        not missing
        and summary["compatibility"]["has_tool_results"]
        and bool(summary["schema_sections_present"])
    )
    return summary


def write_observation(summary: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"real_trace_schema_observation_{timestamp}.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def print_compact_summary(summary: dict[str, Any]) -> None:
    print(f"trace_source={summary.get('trace_source')}")
    print(f"event_count={summary.get('event_count')}")
    print(f"tool_result_count={summary.get('tool_result_count')}")
    print(f"tool_names={summary.get('tool_names')}")
    print(f"financial_statement_types_found={summary.get('financial_statement_types_found')}")
    print(f"has_final_answer={summary.get('has_final_answer')}")
    print(f"schema_generated={summary.get('schema_generated')}")
    print(f"missing_sections={summary.get('missing_sections')}")
    print(f"collector_warnings={summary.get('collector_warnings')}")
    print(f"compatibility={summary.get('compatibility')}")
    if summary.get("error"):
        print(f"error={summary.get('error')}")


def _event_type(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("type") or "")


def _tool_name(event: dict[str, Any]) -> str:
    return str(event.get("tool_name") or event.get("tool") or "")


def _decode_result(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("result")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _financial_statement_types(tool_results: list[dict[str, Any]]) -> list[str]:
    statements: set[str] = set()
    for event in tool_results:
        if _tool_name(event) != "get_financial_statements":
            continue
        result = _decode_result(event)
        statement = str(
            result.get("statement_type")
            or result.get("statement")
            or result.get("type")
            or (event.get("args") or {}).get("statement")
            or ""
        )
        if statement:
            statements.add(statement)
    return sorted(statements)


def _compact_data_confidence(confidence: dict[str, Any]) -> dict[str, Any]:
    market = confidence.get("market_data") if isinstance(confidence.get("market_data"), dict) else {}
    financial = confidence.get("financial_data") if isinstance(confidence.get("financial_data"), dict) else {}
    warnings = confidence.get("warnings") if isinstance(confidence.get("warnings"), list) else []
    return {
        "market_status": market.get("status"),
        "market_provider": market.get("provider"),
        "market_source": market.get("source"),
        "financial_status": financial.get("status"),
        "financial_provider": financial.get("provider"),
        "financial_source": financial.get("source"),
        "financial_period_end_date": financial.get("period_end_date"),
        "warning_count": len(warnings),
        "warnings": warnings[:20],
    }


def main() -> int:
    args = parse_args()
    trace_dir, meta = resolve_trace_source(
        trace_path=args.trace_path,
        run_id=args.run_id,
        session_id=args.session_id,
    )
    summary = observe_trace_to_schema(
        trace_dir=trace_dir,
        symbol=args.symbol,
        run_id=meta.get("run_id", ""),
        session_id=meta.get("session_id", ""),
        limit_events=args.limit_events,
    )
    if meta.get("trace_source") and not summary.get("trace_source"):
        summary["trace_source"] = meta["trace_source"]
    print_compact_summary(summary)

    output_dir = (ROOT / args.output_dir).resolve()
    path = write_observation(summary, output_dir)
    print(f"observation_json={path}")
    return 0 if summary.get("compatibility", {}).get("can_read_trace") else 1


if __name__ == "__main__":
    raise SystemExit(main())
