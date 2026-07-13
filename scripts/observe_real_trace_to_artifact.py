#!/usr/bin/env python3
"""Read one existing trace and write a local-only research artifact observation."""

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
from src.reports import generate_research_artifact  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe one existing trace as a local-only schema artifact."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", default="", help="Existing run id under agent/runs.")
    group.add_argument("--trace-path", default="", help="Existing trace.jsonl or parent directory.")
    parser.add_argument("--symbol", required=True, help="Explicit confirmed symbol, e.g. 300750.SZ.")
    parser.add_argument("--output-dir", default="local_reports", help="Ignored output directory.")
    return parser.parse_args()


def resolve_trace_dir(*, run_id: str = "", trace_path: str = "", root: Path = ROOT) -> Path:
    if run_id:
        return root / "agent" / "runs" / run_id
    path = Path(trace_path).expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    return path.parent if path.name == "trace.jsonl" else path


def observe_trace_to_artifact(
    *,
    trace_dir: Path,
    run_id: str,
    symbol: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Read a trace directory and return a compact summary plus artifact envelope."""

    trace_file = trace_dir / "trace.jsonl"
    summary: dict[str, Any] = {
        "trace_source": str(trace_dir),
        "run_id": run_id,
        "event_count": 0,
        "tool_result_count": 0,
        "tool_names": [],
        "artifact_generated": False,
        "error": "",
    }
    if not trace_file.exists():
        summary["error"] = f"trace.jsonl not found: {trace_file}"
        return summary, None

    events = TraceWriter.read(
        trace_dir,
        resolve_offloads=True,
        resolve_fields={"result", "content", "prompt", "structured_payload"},
    )
    summary["event_count"] = len(events)
    tool_results = [event for event in events if _event_type(event) == "tool_result"]
    summary["tool_result_count"] = len(tool_results)
    summary["tool_names"] = sorted({_tool_name(event) for event in tool_results if _tool_name(event)})
    artifact = generate_research_artifact(
        run_id=run_id,
        trace_events=events,
        input_symbol=symbol,
        metadata={"generator_version": "observation-1.0"},
    )
    summary["artifact_generated"] = artifact["artifact_meta"]["status"] != "failed"
    summary["artifact_status"] = artifact["artifact_meta"]["status"]
    summary["artifact_errors"] = list(artifact["errors"])
    summary["schema_version"] = artifact["schema_version"]
    report = artifact.get("research_report")
    if isinstance(report, dict):
        summary["report_sections"] = sorted(report.keys())
        summary["missing_sections"] = [
            section
            for section in ("market_snapshot", "financial_health", "data_confidence", "limitations")
            if section not in report
        ]
        summary["financial_health_status"] = report.get("financial_health", {}).get("status")
        summary["collector_warnings"] = list(
            report.get("data_confidence", {}).get("warnings", [])
        )
        financial = report.get("data_confidence", {}).get("financial_data", {})
        if isinstance(financial, dict):
            summary["financial_data_confidence"] = {
                "provider": financial.get("provider"),
                "source": financial.get("source"),
                "upstream": financial.get("upstream"),
                "warnings": financial.get("warnings", []),
            }
    return summary, artifact


def write_observation_artifact(artifact: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"research_schema_artifact_observation_{timestamp}.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _event_type(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("type") or "")


def _tool_name(event: dict[str, Any]) -> str:
    return str(event.get("tool_name") or event.get("tool") or "")


def main() -> int:
    args = parse_args()
    trace_dir = resolve_trace_dir(run_id=args.run_id, trace_path=args.trace_path)
    run_id = args.run_id or trace_dir.name
    summary, artifact = observe_trace_to_artifact(
        trace_dir=trace_dir,
        run_id=run_id,
        symbol=args.symbol,
    )
    print(f"trace_source={summary['trace_source']}")
    print(f"event_count={summary['event_count']}")
    print(f"tool_result_count={summary['tool_result_count']}")
    print(f"tool_names={summary['tool_names']}")
    print(f"artifact_status={summary.get('artifact_status', '')}")
    print(f"artifact_errors={summary.get('artifact_errors', [])}")
    print(f"report_sections={summary.get('report_sections', [])}")
    print(f"missing_sections={summary.get('missing_sections', [])}")
    print(f"financial_health_status={summary.get('financial_health_status', '')}")
    print(f"collector_warning_count={len(summary.get('collector_warnings', []))}")
    print(f"financial_data_confidence={summary.get('financial_data_confidence', {})}")
    if artifact is None:
        print(f"error={summary['error']}")
        return 1
    output_path = write_observation_artifact(artifact, (ROOT / args.output_dir).resolve())
    print(f"observation_artifact={output_path}")
    return 0 if summary["artifact_generated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
