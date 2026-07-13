from __future__ import annotations

import unittest

from src.reports import generate_research_artifact
from src.reports.financial_pipeline import normalize_financial_results_for_report
from src.reports.trace_collector import build_research_report_from_trace_events


SYMBOL = "300750.SZ"


def eastmoney_payload(statement: str) -> dict:
    return {
        "ok": True,
        "source": "eastmoney",
        "statement": statement,
        "period": "annual",
        "data": {SYMBOL: {"periods": [{"REPORT_DATE": "2026-03-31", "VALUE": 1}]}},
    }


def metadata() -> dict:
    return {"provider": "eastmoney", "source": "eastmoney_financial_report", "upstream": "eastmoney"}


def financial_event(statement: str) -> dict:
    return {
        "type": "tool_result",
        "tool": "get_financial_statements",
        "status": "ok",
        "result": "legacy financial text",
        "structured_payload": eastmoney_payload(statement),
        "metadata": metadata(),
    }


def market_event() -> dict:
    return {
        "type": "tool_result",
        "tool": "get_market_data",
        "status": "ok",
        "result": {
            "ok": True,
            "data": {SYMBOL: [{"date": "2026-07-10", "close": 200.0}]},
            "_data_quality": {SYMBOL: {"provider": "fixture_market", "source": "fixture", "latest_data_date": "2026-07-10", "warnings": []}},
        },
    }


class FinancialNormalizerPipelineTests(unittest.TestCase):
    def complete_events(self) -> list[dict]:
        return [
            market_event(),
            financial_event("income"),
            financial_event("balance"),
            financial_event("cashflow"),
            {"type": "answer", "content": "Fixture interpretation."},
        ]

    def test_eastmoney_structured_payload_generates_complete_financial_health(self) -> None:
        report = build_research_report_from_trace_events(
            self.complete_events(), input_symbol=SYMBOL, run_id="periods-fixture"
        )

        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(report["data_confidence"]["financial_data"]["provider"], "eastmoney")
        self.assertEqual(report["data_confidence"]["financial_data"]["reporting_period"], "2026-03-31")

    def test_legacy_canonical_rows_pass_through_unchanged(self) -> None:
        legacy = {
            "ok": True,
            "statement_type": "income",
            "provider": "legacy_provider",
            "source": "legacy_source",
            "data": {SYMBOL: [{"report_date": "2026-03-31", "VALUE": 1}]},
        }
        normalized, warnings = normalize_financial_results_for_report([legacy])

        self.assertEqual(normalized, [legacy])
        self.assertEqual(warnings, [])

    def test_malformed_periods_envelope_is_partial_with_warning(self) -> None:
        broken = eastmoney_payload("income")
        broken["data"] = {SYMBOL: {}}
        events = [market_event(), {**financial_event("income"), "structured_payload": broken}, {"type": "answer", "content": "Fixture."}]
        report = build_research_report_from_trace_events(events, input_symbol=SYMBOL)

        self.assertEqual(report["financial_health"]["status"], "missing")
        self.assertIn("financial_normalizer:income:missing_periods", report["data_confidence"]["warnings"])

    def test_mixed_provider_results_remain_separate(self) -> None:
        primary = eastmoney_payload("income")
        fallback = {
            "ok": True,
            "statement_type": "income",
            "provider": "a_stock_data",
            "source": "sina_financial_report",
            "data": {SYMBOL: [{"report_date": "2026-03-31", "VALUE": 2}]},
        }
        normalized, _ = normalize_financial_results_for_report([primary, fallback])

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0]["data"][SYMBOL][0]["VALUE"], 1)
        self.assertEqual(normalized[1]["data"][SYMBOL][0]["VALUE"], 2)
        self.assertEqual(normalized[1]["provider"], "a_stock_data")

    def test_pipeline_events_generate_complete_artifact(self) -> None:
        artifact = generate_research_artifact(
            run_id="periods-artifact-fixture",
            trace_events=self.complete_events(),
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")


if __name__ == "__main__":
    unittest.main()
