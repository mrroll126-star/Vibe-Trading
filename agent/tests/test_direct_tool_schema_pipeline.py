from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from src.reports import build_research_report
from src.tools.financial_statements_tool import FinancialStatementsTool


SYMBOL = "600519.SH"


FORCED_PRIMARY_FAILURE = {
    "ok": False,
    "error": "forced_primary_failure_for_schema_pipeline_test",
    "data": [],
}


def market_result(symbol: str = SYMBOL) -> dict:
    return {
        "ok": True,
        "data": {symbol: [{"date": "2026-07-10", "close": 1500.5}]},
        "_data_quality": {
            symbol: {
                "provider": "mock_market_provider",
                "source": "mock_market_data",
                "latest_data_date": "2026-07-10",
                "warnings": [],
            }
        },
    }


def fallback_payload(statement: str) -> dict:
    rows = {
        "income": [{"报告期": "2026-03-31", "营业收入": 547.03, "净利润": 281.54}],
        "balance": [{"报告期": "2026-03-31", "总资产": 3000.0, "总负债": 500.0}],
        "cashflow": [{"报告期": "2026-03-31", "经营活动现金流": 260.0}],
    }
    return {
        "ok": True,
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "data": rows.get(statement, []),
    }


def execute_statement(symbol: str, statement: str, *, fallback_ok: bool = True) -> dict:
    def _mock_fetch(symbol_arg: str, statement_type: str | None = None, **_: object) -> dict:
        if not fallback_ok:
            return {
                "ok": False,
                "error": "mock_fallback_missing",
                "source": "sina_financial_report",
                "upstream": "a-stock-data",
                "data": [],
            }
        return fallback_payload(statement_type or statement)

    with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=FORCED_PRIMARY_FAILURE,
        ):
            with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", side_effect=_mock_fetch):
                return json.loads(
                    FinancialStatementsTool().execute(
                        code=symbol,
                        statement=statement,
                        period="annual",
                    )
                )


class DirectToolSchemaPipelineTests(unittest.TestCase):
    def test_financial_tool_output_to_schema_success(self) -> None:
        results = [execute_statement(SYMBOL, statement) for statement in ("income", "balance", "cashflow")]

        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=results,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["symbol"]["normalized_symbol"], SYMBOL)
        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(len(report["financial_health"]["statements"]), 3)
        self.assertEqual(report["data_confidence"]["financial_data"]["provider"], "a_stock_data")
        self.assertEqual(report["data_confidence"]["financial_data"]["source"], "sina_financial_report")
        self.assertEqual(report["data_confidence"]["financial_data"]["period_end_date"], "2026-03-31")
        self.assertIn("a_stock_data_fallback_used", report["data_confidence"]["warnings"])

    def test_financial_tool_fallback_missing_to_schema_warning(self) -> None:
        result = execute_statement(SYMBOL, "income", fallback_ok=False)

        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=[result],
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["financial_health"]["status"], "missing")
        warnings = report["data_confidence"]["warnings"]
        self.assertIn("a_stock_data_fallback_failed", warnings)
        self.assertIn("income_statement_missing", warnings)

    def test_index_and_etf_do_not_enter_financial_schema(self) -> None:
        for symbol in ("000300.SH", "510300.SH"):
            with self.subTest(symbol=symbol):
                result = execute_statement(symbol, "income")

                report = build_research_report(
                    input_symbol=symbol,
                    market_result=market_result(symbol),
                    financial_results=[result],
                    generated_at="2026-07-11T00:00:00+00:00",
                )

                self.assertEqual(report["financial_health"]["status"], "blocked")
                self.assertEqual(report["financial_health"]["statements"], [])
                self.assertTrue(
                    any("company_financials_not_applicable_for" in item for item in report["data_confidence"]["warnings"])
                )

    def test_data_quality_missing_adds_warning(self) -> None:
        result = {
            "ok": True,
            "provider": "a_stock_data",
            "source": "sina_financial_report",
            "upstream": "a-stock-data",
            "statement_type": "income",
            "period": "annual",
            "data": {SYMBOL: [{"report_date": "2026-03-31", "revenue": 547.03}]},
        }

        report = build_research_report(
            input_symbol=SYMBOL,
            market_result=market_result(),
            financial_results=[result],
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertIn("income_data_quality_missing", report["data_confidence"]["warnings"])
        self.assertEqual(report["financial_health"]["statements"][0]["latest_data_date"], "2026-03-31")


if __name__ == "__main__":
    unittest.main()
