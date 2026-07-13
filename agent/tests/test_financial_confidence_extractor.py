from __future__ import annotations

import unittest

from src.reports.financial_confidence import (
    FinancialConfidenceError,
    extract_financial_confidence,
)


def statement(
    statement_type: str,
    *,
    provider: str = "eastmoney",
    source: str = "eastmoney_financial_report",
    period: str = "2026-03-31",
    fallback: bool = False,
    ok: bool = True,
) -> dict:
    return {
        "ok": ok,
        "provider": provider,
        "source": source,
        "upstream": "sina" if fallback else "eastmoney",
        "statement_type": statement_type,
        "latest_data_date": period,
        "fallback": fallback,
        "data": [{"report_date": period, "value": 1}] if ok else [],
    }


def complete_results() -> dict:
    return {
        "income": statement("income"),
        "balance": statement("balance"),
        "cashflow": statement("cashflow"),
    }


class FinancialConfidenceExtractorTests(unittest.TestCase):
    def test_complete_three_statements_are_complete(self) -> None:
        result = extract_financial_confidence(complete_results())
        self.assertEqual(result["financial_health"]["status"], "complete")
        self.assertEqual(result["data_confidence"]["financial_data"]["reporting_period"], "2026-03-31")
        self.assertEqual(len(result["financial_health"]["statement_level_confidence"]), 3)
        self.assertFalse(result["financial_health"]["fallback_status"]["fallback_used"])

    def test_fallback_preserves_warning_and_provenance(self) -> None:
        results = complete_results()
        results["balance"] = statement(
            "balance", provider="a_stock_data", source="sina_financial_report", fallback=True
        )
        result = extract_financial_confidence(results)
        balance = result["data_confidence"]["financial_data"]["statements"]["balance"]
        self.assertTrue(balance["fallback_used"])
        self.assertEqual(balance["provider"], "a_stock_data")
        self.assertIn("fallback_provider_used", result["warnings"])
        self.assertTrue(result["data_confidence"]["financial_data"]["fallback_used"])

    def test_failed_statement_makes_combined_status_partial(self) -> None:
        results = complete_results()
        results["cashflow"] = {"ok": False, "error": "forced_failure", "data": []}
        result = extract_financial_confidence(results)
        self.assertEqual(result["financial_health"]["status"], "partial")
        cashflow = result["data_confidence"]["financial_data"]["statements"]["cashflow"]
        self.assertEqual(cashflow["status"], "failed")
        self.assertIn("forced_failure", result["warnings"])

    def test_missing_statement_makes_combined_status_partial(self) -> None:
        results = complete_results()
        del results["cashflow"]
        result = extract_financial_confidence(results)
        cashflow = result["data_confidence"]["financial_data"]["statements"]["cashflow"]
        self.assertEqual(result["financial_health"]["status"], "partial")
        self.assertEqual(cashflow["status"], "missing")
        self.assertIn("cashflow_statement_missing", result["warnings"])

    def test_missing_provider_and_source_are_warnings(self) -> None:
        results = complete_results()
        results["income"] = statement("income", provider="", source="")
        result = extract_financial_confidence(results)
        income = result["data_confidence"]["financial_data"]["statements"]["income"]
        self.assertEqual(income["status"], "partial")
        self.assertIn("provider_missing", result["warnings"])
        self.assertIn("source_missing", result["warnings"])

    def test_missing_reporting_period_is_warning(self) -> None:
        results = complete_results()
        results["income"] = statement("income", period="")
        result = extract_financial_confidence(results)
        income = result["data_confidence"]["financial_data"]["statements"]["income"]
        self.assertEqual(income["reporting_period_status"], "missing_period")
        self.assertIn("missing_reporting_period", result["warnings"])
        self.assertEqual(result["financial_health"]["status"], "partial")

    def test_index_and_etf_are_rejected(self) -> None:
        for asset_type in ("index", "etf"):
            with self.subTest(asset_type=asset_type):
                with self.assertRaises(FinancialConfidenceError):
                    extract_financial_confidence(complete_results(), asset_type=asset_type)


if __name__ == "__main__":
    unittest.main()
