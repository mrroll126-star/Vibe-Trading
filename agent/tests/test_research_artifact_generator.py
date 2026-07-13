from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.reports import generate_research_artifact


SYMBOL = "600519.SH"
GENERATED_AT = "2026-07-13T00:00:00+00:00"


def market_event(symbol: str = SYMBOL) -> dict:
    return {
        "type": "tool_result",
        "tool": "get_market_data",
        "status": "ok",
        "result": {
            "ok": True,
            "data": {symbol: [{"date": "2026-07-10", "close": 1500.5}]},
            "_data_quality": {
                symbol: {
                    "provider": "fixture_market",
                    "source": "fixture_market_data",
                    "latest_data_date": "2026-07-10",
                    "warnings": [],
                }
            },
        },
    }


def financial_event(statement_type: str, symbol: str = SYMBOL) -> dict:
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
            "data": {symbol: [{"report_date": "2026-03-31", "value": 1}]},
            "_data_quality": {
                symbol: {
                    "provider": "a_stock_data",
                    "source": "sina_financial_report",
                    "upstream": "sina",
                    "latest_data_date": "2026-03-31",
                    "warnings": ["a_stock_data_fallback_used"],
                }
            },
        },
    }


def complete_events(symbol: str = SYMBOL) -> list[dict]:
    return [
        {"type": "start"},
        market_event(symbol),
        financial_event("income", symbol),
        financial_event("balance", symbol),
        financial_event("cashflow", symbol),
        {"type": "answer", "content": "Fixture answer."},
    ]


class ResearchArtifactGeneratorTests(unittest.TestCase):
    def artifact(self, events: list[dict] | None, symbol: str = SYMBOL) -> dict:
        return generate_research_artifact(
            run_id="fixture-run",
            trace_events=events,
            input_symbol=symbol,
            metadata={"generated_at": GENERATED_AT, "generator_version": "fixture-1"},
        )

    def test_complete_trace_generates_complete_artifact(self) -> None:
        artifact = self.artifact(complete_events())
        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")
        self.assertEqual(artifact["errors"], [])

    def test_missing_financial_data_generates_partial_artifact(self) -> None:
        events = [event for event in complete_events() if event.get("tool") != "get_financial_statements"]
        artifact = self.artifact(events)
        self.assertEqual(artifact["artifact_meta"]["status"], "partial")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "missing")

    def test_missing_market_data_generates_partial_artifact(self) -> None:
        events = [event for event in complete_events() if event.get("tool") != "get_market_data"]
        artifact = self.artifact(events)
        self.assertEqual(artifact["artifact_meta"]["status"], "partial")
        self.assertEqual(artifact["research_report"]["market_snapshot"]["status"], "missing")

    def test_empty_trace_generates_failed_artifact(self) -> None:
        artifact = self.artifact([])
        self.assertEqual(artifact["artifact_meta"]["status"], "failed")
        self.assertEqual(artifact["research_report"], {})
        self.assertIn("trace_events_missing_or_empty", artifact["errors"])

    def test_invalid_symbol_generates_failed_artifact(self) -> None:
        artifact = self.artifact(complete_events(), symbol="贵州茅台")
        self.assertEqual(artifact["artifact_meta"]["status"], "failed")
        self.assertIn("research_report_build_failed", artifact["errors"])

    def test_artifact_fields_are_json_serializable_in_temp_directory(self) -> None:
        artifact = self.artifact(complete_events())
        self.assertEqual(artifact["schema_version"], "1.0")
        self.assertEqual(artifact["artifact_meta"]["run_id"], "fixture-run")
        self.assertEqual(artifact["artifact_meta"]["generated_at"], GENERATED_AT)
        self.assertEqual(artifact["artifact_meta"]["generator_version"], "fixture-1")
        self.assertIn("research_report", artifact)
        with tempfile.TemporaryDirectory() as directory:
            artifact_path = Path(directory) / "research_schema.json"
            artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(json.loads(artifact_path.read_text(encoding="utf-8"))["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
