from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.observe_real_trace_to_artifact import observe_trace_to_artifact, write_observation_artifact


SYMBOL = "600519.SH"


def write_trace(trace_dir: Path, events: list[dict]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )


def market_event() -> dict:
    return {
        "type": "tool_result",
        "tool": "get_market_data",
        "status": "ok",
        "result": {
            "ok": True,
            "data": {SYMBOL: [{"date": "2026-07-10", "close": 1500.5}]},
            "_data_quality": {
                SYMBOL: {
                    "provider": "fixture_market",
                    "source": "fixture_market_data",
                    "latest_data_date": "2026-07-10",
                    "warnings": [],
                }
            },
        },
    }


def financial_event(statement_type: str) -> dict:
    return {
        "type": "tool_result",
        "tool": "get_financial_statements",
        "status": "ok",
        "result": {
            "ok": True,
            "statement_type": statement_type,
            "provider": "a_stock_data",
            "source": "sina_financial_report",
            "upstream": "sina",
            "fallback": True,
            "data": {SYMBOL: [{"report_date": "2026-03-31", "value": 1}]},
            "_data_quality": {
                SYMBOL: {
                    "provider": "a_stock_data",
                    "source": "sina_financial_report",
                    "upstream": "sina",
                    "latest_data_date": "2026-03-31",
                    "warnings": ["a_stock_data_fallback_used"],
                }
            },
        },
    }


def complete_events() -> list[dict]:
    return [
        {"type": "start"},
        market_event(),
        financial_event("income"),
        financial_event("balance"),
        financial_event("cashflow"),
        {"type": "answer", "content": "Fixture answer."},
    ]


class RealTraceArtifactObservationTests(unittest.TestCase):
    def test_invalid_trace_path_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary, artifact = observe_trace_to_artifact(
                trace_dir=Path(directory) / "missing",
                run_id="missing-run",
                symbol=SYMBOL,
            )

        self.assertIsNone(artifact)
        self.assertIn("trace.jsonl not found", summary["error"])

    def test_empty_trace_returns_failed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace_dir = Path(directory) / "trace"
            write_trace(trace_dir, [])
            summary, artifact = observe_trace_to_artifact(
                trace_dir=trace_dir,
                run_id="empty-run",
                symbol=SYMBOL,
            )

        self.assertIsNotNone(artifact)
        self.assertEqual(summary["artifact_status"], "failed")
        self.assertIn("trace_events_missing_or_empty", artifact["errors"])

    def test_valid_trace_returns_complete_compatible_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace_dir = Path(directory) / "trace"
            write_trace(trace_dir, complete_events())
            summary, artifact = observe_trace_to_artifact(
                trace_dir=trace_dir,
                run_id="fixture-run",
                symbol=SYMBOL,
            )

        self.assertTrue(summary["artifact_generated"])
        self.assertEqual(artifact["schema_version"], "1.0")
        self.assertEqual(artifact["artifact_meta"]["run_id"], "fixture-run")
        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertIn("financial_health", artifact["research_report"])
        financial = artifact["research_report"]["data_confidence"]["financial_data"]
        self.assertEqual(financial["provider"], "a_stock_data")
        self.assertEqual(financial["source"], "sina_financial_report")
        self.assertEqual(financial["upstream"], "sina")

    def test_observation_artifact_writes_only_to_temp_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace_dir = Path(directory) / "trace"
            write_trace(trace_dir, complete_events())
            _, artifact = observe_trace_to_artifact(
                trace_dir=trace_dir,
                run_id="fixture-run",
                symbol=SYMBOL,
            )
            output_dir = Path(directory) / "local_reports"
            path = write_observation_artifact(artifact, output_dir)
            self.assertEqual(path.parent, output_dir)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["schema_version"],
                "1.0",
            )


if __name__ == "__main__":
    unittest.main()

