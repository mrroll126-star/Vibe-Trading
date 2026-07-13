from __future__ import annotations

import unittest

from src.reports import build_research_report_from_trace_events


SYMBOL = "600519.SH"


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


def financial_event(
    statement_type: str,
    *,
    symbol: str = SYMBOL,
    provider: str = "eastmoney",
    source: str = "eastmoney_financial_report",
    fallback: bool = False,
    period: str = "2026-03-31",
) -> dict:
    return {
        "type": "tool_result",
        "tool": "get_financial_statements",
        "status": "ok",
        "result": {
            "ok": True,
            "statement_type": statement_type,
            "provider": provider,
            "source": source,
            "upstream": "sina" if fallback else "eastmoney",
            "fallback": fallback,
            "data": {symbol: [{"report_date": period, "value": 1}]},
            "_data_quality": {
                symbol: {
                    "provider": provider,
                    "source": source,
                    "upstream": "sina" if fallback else "eastmoney",
                    "latest_data_date": period,
                    "warnings": ["a_stock_data_fallback_used"] if fallback else [],
                }
            },
        },
    }


def complete_events(symbol: str = SYMBOL) -> list[dict]:
    return [
        {"type": "start"},
        market_event(symbol),
        financial_event("income", symbol=symbol),
        financial_event("balance", symbol=symbol),
        financial_event("cashflow", symbol=symbol),
        {"type": "answer", "content": "Fixture answer."},
    ]


class FinancialConfidenceIntegrationTests(unittest.TestCase):
    def test_complete_trace_generates_complete_financial_schema(self) -> None:
        report = build_research_report_from_trace_events(
            complete_events(), input_symbol=SYMBOL, generated_at="2026-07-13T00:00:00+00:00"
        )
        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(len(report["financial_health"]["statement_level_confidence"]), 3)
        self.assertIn("financial_data", report["data_confidence"])
        self.assertEqual(report["data_confidence"]["financial_data"]["status"], "complete")

    def test_fallback_trace_preserves_fallback_status_and_warning(self) -> None:
        events = complete_events()
        events[3] = financial_event(
            "balance", provider="a_stock_data", source="sina_financial_report", fallback=True
        )
        report = build_research_report_from_trace_events(
            events, input_symbol=SYMBOL, generated_at="2026-07-13T00:00:00+00:00"
        )
        financial = report["data_confidence"]["financial_data"]
        self.assertTrue(financial["fallback_used"])
        self.assertTrue(financial["statements"]["balance"]["fallback_used"])
        self.assertIn("fallback_provider_used", report["data_confidence"]["warnings"])
        self.assertIn("a_stock_data_fallback_used", report["data_confidence"]["warnings"])

    def test_missing_cashflow_makes_financial_schema_partial(self) -> None:
        events = complete_events()[:4] + [complete_events()[-1]]
        report = build_research_report_from_trace_events(
            events, input_symbol=SYMBOL, generated_at="2026-07-13T00:00:00+00:00"
        )
        self.assertEqual(report["financial_health"]["status"], "partial")
        self.assertEqual(
            report["data_confidence"]["financial_data"]["statements"]["cashflow"]["status"],
            "missing",
        )

    def test_missing_provider_and_source_remain_visible(self) -> None:
        events = complete_events()
        events[2] = financial_event("income", provider="", source="")
        report = build_research_report_from_trace_events(
            events, input_symbol=SYMBOL, generated_at="2026-07-13T00:00:00+00:00"
        )
        self.assertEqual(report["financial_health"]["status"], "partial")
        self.assertIn("provider_missing", report["data_confidence"]["warnings"])
        self.assertIn("source_missing", report["data_confidence"]["warnings"])

    def test_index_and_etf_keep_financial_confidence_blocked(self) -> None:
        for symbol in ("000300.SH", "510300.SH"):
            with self.subTest(symbol=symbol):
                report = build_research_report_from_trace_events(
                    complete_events(symbol),
                    input_symbol=symbol,
                    generated_at="2026-07-13T00:00:00+00:00",
                )
                self.assertEqual(report["financial_health"]["status"], "blocked")
                self.assertEqual(report["financial_health"]["statements"], [])
                self.assertNotIn("statement_level_confidence", report["financial_health"])

    def test_missing_final_answer_keeps_schema_and_placeholder_memo(self) -> None:
        events = [event for event in complete_events() if event.get("type") != "answer"]
        report = build_research_report_from_trace_events(
            events, input_symbol=SYMBOL, generated_at="2026-07-13T00:00:00+00:00"
        )
        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(report["investment_memo"]["thesis"], "")
        self.assertIn("final_answer_missing_from_trace", report["data_confidence"]["warnings"])


if __name__ == "__main__":
    unittest.main()
