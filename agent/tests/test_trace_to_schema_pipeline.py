from __future__ import annotations

import json
import unittest

from src.reports import ReportBuildError, build_research_report_from_trace_events


SYMBOL = "600519.SH"


def market_event(symbol: str = SYMBOL) -> dict:
    return {
        "event_type": "tool_result",
        "tool_name": "get_market_data",
        "args": {"symbol": symbol},
        "status": "success",
        "timestamp": "2026-07-11T01:00:00Z",
        "result": {
            "ok": True,
            "data": {
                symbol: [
                    {
                        "date": "2026-07-10",
                        "close": 1500.5,
                        "change_pct": 1.2,
                        "volume": 1000000,
                    }
                ]
            },
            "_data_quality": {
                symbol: {
                    "provider": "mock_market_provider",
                    "source": "mock_market_data",
                    "latest_data_date": "2026-07-10",
                    "freshness_status": "fresh",
                    "warnings": [],
                }
            },
        },
    }


def financial_event(statement: str, metrics: dict, symbol: str = SYMBOL) -> dict:
    return {
        "type": "tool_result",
        "tool": "get_financial_statements",
        "args": {"code": symbol, "statement": statement},
        "status": "ok",
        "ts": 1783731600,
        "result": json.dumps(
            {
                "ok": True,
                "provider": "a_stock_data",
                "source": "sina_financial_report",
                "upstream": "a-stock-data",
                "statement_type": statement,
                "period": "annual",
                "data": {symbol: [metrics]},
                "_data_quality": {
                    symbol: {
                        "provider": "a_stock_data",
                        "source": "sina_financial_report",
                        "upstream": "a-stock-data",
                        "latest_data_date": "2026-03-31",
                        "warnings": [
                            "primary_financials_unavailable",
                            "a_stock_data_fallback_used",
                        ],
                    }
                },
            },
            ensure_ascii=False,
        ),
    }


def final_answer_event() -> dict:
    return {
        "type": "answer",
        "content": "基于已验证工具数据生成的占位分析，不新增价格或财务事实。",
    }


def complete_events(symbol: str = SYMBOL) -> list[dict]:
    return [
        {"type": "start", "prompt": "Analyze 600519.SH"},
        market_event(symbol),
        financial_event("income", {"report_date": "2026-03-31", "revenue": 547.03, "net_profit": 281.54}, symbol),
        financial_event("balance", {"report_date": "2026-03-31", "total_assets": 3000.0}, symbol),
        financial_event("cashflow", {"report_date": "2026-03-31", "operating_cash_flow": 260.0}, symbol),
        {"event_type": "ignored_custom_event", "payload": "ignored"},
        final_answer_event(),
    ]


class TraceToSchemaPipelineTests(unittest.TestCase):
    def test_complete_trace_fixture_to_schema_success(self) -> None:
        report = build_research_report_from_trace_events(
            complete_events(),
            input_symbol=SYMBOL,
            run_id="trace-fixture-run",
            generated_at="2026-07-11T00:00:00+00:00",
            provider="mock_llm",
            model="mock_model",
        )

        self.assertEqual(report["research_meta"]["run_id"], "trace-fixture-run")
        self.assertEqual(report["research_meta"]["raw_event_count"], 7)
        self.assertEqual(report["symbol"]["normalized_symbol"], SYMBOL)
        self.assertEqual(report["market_snapshot"]["status"], "available")
        self.assertEqual(report["financial_health"]["status"], "available")
        self.assertEqual(len(report["financial_health"]["statements"]), 3)
        self.assertEqual(report["data_confidence"]["financial_data"]["provider"], "a_stock_data")
        self.assertEqual(report["data_confidence"]["financial_data"]["source"], "sina_financial_report")
        self.assertIn("a_stock_data_fallback_used", report["data_confidence"]["warnings"])
        self.assertIn("event_5_ignored_unknown_type_ignored_custom_event", report["data_confidence"]["warnings"])
        self.assertIn("target_price", report["limitations"]["unsupported"])

    def test_missing_market_data_marks_market_snapshot_missing(self) -> None:
        events = [event for event in complete_events() if event.get("tool_name") != "get_market_data"]

        report = build_research_report_from_trace_events(
            events,
            input_symbol=SYMBOL,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["market_snapshot"]["status"], "missing")
        self.assertIn("market_data_missing", report["data_confidence"]["warnings"])
        self.assertIn("market_data_missing_from_trace", report["data_confidence"]["warnings"])

    def test_missing_financial_data_marks_financial_health_missing(self) -> None:
        report = build_research_report_from_trace_events(
            [market_event(), final_answer_event()],
            input_symbol=SYMBOL,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["financial_health"]["status"], "missing")
        self.assertEqual(report["financial_health"]["statements"], [])
        self.assertIn("financial_data_missing_from_trace", report["data_confidence"]["warnings"])
        self.assertEqual(report["financial_health"]["summary"]["interpretation"], "")

    def test_fallback_financial_data_preserves_data_confidence(self) -> None:
        report = build_research_report_from_trace_events(
            complete_events(),
            input_symbol=SYMBOL,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        financial = report["data_confidence"]["financial_data"]
        self.assertEqual(financial["provider"], "a_stock_data")
        self.assertEqual(financial["source"], "sina_financial_report")
        self.assertEqual(financial["period_end_date"], "2026-03-31")
        self.assertIn("primary_financials_unavailable", report["data_confidence"]["warnings"])
        self.assertIn("a_stock_data_fallback_used", report["data_confidence"]["warnings"])

    def test_failed_tool_event_preserves_warning(self) -> None:
        failed_income = {
            "event_type": "tool_result",
            "tool_name": "get_financial_statements",
            "status": "error",
            "result": {
                "ok": False,
                "statement_type": "income",
                "error": "forced_tool_failure",
                "warnings": ["provider_failed"],
                "_data_quality": {
                    SYMBOL: {
                        "provider": "a_stock_data",
                        "source": "sina_financial_report",
                        "warnings": ["fallback_failed"],
                    }
                },
            },
        }

        report = build_research_report_from_trace_events(
            [market_event(), failed_income, final_answer_event()],
            input_symbol=SYMBOL,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        warnings = report["data_confidence"]["warnings"]
        self.assertEqual(report["financial_health"]["status"], "missing")
        self.assertIn("forced_tool_failure", warnings)
        self.assertIn("provider_failed", warnings)
        self.assertIn("get_financial_statements_status_error", warnings)
        self.assertIn("fallback_failed", warnings)

    def test_invalid_or_ambiguous_symbol_rejected(self) -> None:
        with self.assertRaises(ReportBuildError):
            build_research_report_from_trace_events(
                complete_events(),
                input_symbol="贵州茅台",
                generated_at="2026-07-11T00:00:00+00:00",
            )

    def test_final_answer_missing_keeps_facts_and_placeholder_memo(self) -> None:
        events = [event for event in complete_events() if event.get("type") != "answer"]

        report = build_research_report_from_trace_events(
            events,
            input_symbol=SYMBOL,
            generated_at="2026-07-11T00:00:00+00:00",
        )

        self.assertEqual(report["financial_health"]["status"], "available")
        self.assertEqual(report["investment_memo"]["thesis"], "")
        self.assertEqual(report["investment_memo"]["bull_case"], [])
        self.assertIn("final_answer_missing_from_trace", report["data_confidence"]["warnings"])


if __name__ == "__main__":
    unittest.main()
