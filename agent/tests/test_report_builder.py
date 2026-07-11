from __future__ import annotations

import unittest

from src.reports import ReportBuildError, build_research_report


SYMBOL = "600519.SH"


def market_result() -> dict:
    return {
        "ok": True,
        "data": {
            SYMBOL: [
                {
                    "date": "2026-07-10",
                    "close": 1500.5,
                    "change_pct": 1.2,
                    "volume": 1000000,
                    "turnover": 1500500000,
                }
            ]
        },
        "_data_quality": {
            SYMBOL: {
                "provider": "mock_market_provider",
                "source": "mock_market_data",
                "latest_data_date": "2026-07-10",
                "freshness_status": "fresh",
                "warnings": [],
            }
        },
    }


def financial_result(statement: str, metrics: dict) -> dict:
    return {
        "ok": True,
        "provider": "a_stock_data",
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "statement_type": statement,
        "period": "annual",
        "data": {SYMBOL: [metrics]},
        "_data_quality": {
            SYMBOL: {
                "provider": "a_stock_data",
                "source": "sina_financial_report",
                "upstream": "a-stock-data",
                "latest_data_date": "2026-03-31",
                "warnings": ["a_stock_data_fallback_used"],
            }
        },
    }


def full_financial_results() -> list[dict]:
    return [
        financial_result("income", {"report_date": "2026-03-31", "revenue": 547.03, "net_profit": 281.54}),
        financial_result("balance", {"report_date": "2026-03-31", "total_assets": 3000.0, "total_liabilities": 500.0}),
        financial_result("cashflow", {"report_date": "2026-03-31", "operating_cash_flow": 260.0}),
    ]


class ReportBuilderTests(unittest.TestCase):
    def test_complete_mock_data_builds_full_schema(self) -> None:
        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=full_financial_results(),
            interpretation={
                "thesis": "Mock thesis",
                "bull_case": ["Brand strength"],
                "bear_case": ["Growth slowdown"],
                "key_risks": ["Demand risk"],
                "monitor_items": ["Next filing"],
            },
            run_id="mock-run",
            generated_at="2026-07-11T00:00:00+00:00",
            provider="mock_llm",
            model="mock_model",
        )

        self.assertEqual(report["research_meta"]["run_id"], "mock-run")
        self.assertEqual(report["symbol"]["normalized_symbol"], SYMBOL)
        self.assertEqual(report["market_snapshot"]["price"], 1500.5)
        self.assertEqual(report["market_snapshot"]["status"], "available")
        self.assertEqual(len(report["financial_health"]["statements"]), 3)
        self.assertEqual(report["financial_health"]["status"], "available")
        self.assertEqual(report["financial_health"]["statements"][0]["provider"], "a_stock_data")
        self.assertEqual(report["investment_memo"]["bull_case"], ["Brand strength"])
        self.assertEqual(report["data_confidence"]["financial_data"]["source"], "sina_financial_report")
        self.assertIn("a_stock_data_fallback_used", report["data_confidence"]["warnings"])
        self.assertIn("target_price", report["limitations"]["unsupported"])

    def test_missing_financial_data_marks_financial_health_missing(self) -> None:
        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=[],
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["financial_health"]["status"], "missing")
        self.assertEqual(report["financial_health"]["statements"], [])
        self.assertEqual(report["data_confidence"]["financial_data"]["status"], "missing")
        self.assertIn("income_statement_missing", report["data_confidence"]["warnings"])
        self.assertEqual(report["investment_memo"]["thesis"], "")

    def test_provider_failure_lowers_confidence_and_adds_warning(self) -> None:
        failed_income = {
            "ok": False,
            "statement_type": "income",
            "error": "primary_financials_unavailable",
            "warnings": ["a_stock_data_fallback_failed"],
            "_data_quality": {
                SYMBOL: {
                    "provider": "a_stock_data",
                    "source": "sina_financial_report",
                    "latest_data_date": "",
                    "warnings": ["primary_financials_unavailable"],
                }
            },
        }
        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=[failed_income],
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["financial_health"]["status"], "missing")
        warnings = report["data_confidence"]["warnings"]
        self.assertIn("primary_financials_unavailable", warnings)
        self.assertIn("a_stock_data_fallback_failed", warnings)
        self.assertIn("income_statement_missing", warnings)

    def test_invalid_symbol_rejects_generation(self) -> None:
        with self.assertRaises(ReportBuildError):
            build_research_report(
                input_symbol="贵州茅台",
                market_result=market_result(),
                financial_results=full_financial_results(),
            )


if __name__ == "__main__":
    unittest.main()
