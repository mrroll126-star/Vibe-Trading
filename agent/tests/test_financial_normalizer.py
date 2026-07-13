from __future__ import annotations

import unittest

from src.reports import generate_research_artifact
from src.reports.financial_confidence import extract_financial_confidence
from src.reports.financial_normalizer import normalize_financial_statement_payload


SYMBOL = "300750.SZ"


def eastmoney_payload(statement: str, *, include_period: bool = True) -> dict:
    row = {"TOTAL_VALUE": 100}
    if include_period:
        row["REPORT_DATE"] = "2026-03-31"
    return {
        "ok": True,
        "market": "cn",
        "source": "eastmoney",
        "statement": statement,
        "period": "annual",
        "data": {SYMBOL: {"periods": [row]}},
    }


def normalized(statement: str) -> dict:
    return normalize_financial_statement_payload(
        eastmoney_payload(statement),
        metadata={"provider": "eastmoney", "source": "eastmoney_financial_report", "upstream": "eastmoney"},
    )


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


class FinancialNormalizerTests(unittest.TestCase):
    def test_complete_eastmoney_income_is_canonical(self) -> None:
        result = normalized("income")

        self.assertTrue(result["ok"])
        self.assertEqual(result["statement_type"], "income")
        self.assertEqual(result["data"][SYMBOL][0]["report_date"], "2026-03-31")
        self.assertEqual(result["provider"], "eastmoney")
        self.assertEqual(result["source"], "eastmoney_financial_report")

    def test_complete_balance_and_cashflow_are_canonical(self) -> None:
        for statement in ("balance", "cashflow"):
            with self.subTest(statement=statement):
                result = normalized(statement)
                self.assertTrue(result["ok"])
                self.assertEqual(result["statement_type"], statement)
                self.assertEqual(len(result["data"][SYMBOL]), 1)

    def test_missing_period_preserves_row_and_warns(self) -> None:
        result = normalize_financial_statement_payload(
            eastmoney_payload("income", include_period=False),
            metadata={"provider": "eastmoney", "source": "eastmoney_financial_report"},
        )

        self.assertTrue(result["ok"])
        self.assertIn("missing_reporting_period", result["warnings"])
        self.assertEqual(result["data"][SYMBOL][0]["TOTAL_VALUE"], 100)

    def test_missing_metadata_warns(self) -> None:
        result = normalize_financial_statement_payload(eastmoney_payload("income"))

        self.assertIn("provider_missing", result["warnings"])
        self.assertEqual(result["source"], "eastmoney")

    def test_malformed_envelope_is_not_inferred(self) -> None:
        result = normalize_financial_statement_payload({"ok": True, "statement": "income", "data": {SYMBOL: {}}})

        self.assertFalse(result["ok"])
        self.assertIn("missing_periods", result["warnings"])
        self.assertEqual(result["data"], {})

    def test_normalized_results_feed_confidence_and_artifact(self) -> None:
        statements = {statement: normalized(statement) for statement in ("income", "balance", "cashflow")}
        confidence = extract_financial_confidence(statements)
        self.assertEqual(confidence["financial_health"]["status"], "complete")

        events = [market_event()]
        events.extend(
            {"type": "tool_result", "tool": "get_financial_statements", "status": "ok", "result": result}
            for result in statements.values()
        )
        events.append({"type": "answer", "content": "Fixture interpretation."})
        artifact = generate_research_artifact(
            run_id="eastmoney-normalizer-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")


if __name__ == "__main__":
    unittest.main()
