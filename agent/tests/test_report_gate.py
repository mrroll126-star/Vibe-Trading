from __future__ import annotations

import unittest

from src.data_quality import (
    append_data_source_summary,
    detect_time_sensitive_request,
    evaluate_market_data_report_gate,
    format_data_insufficient_report,
)


OFFICIAL_CLOSE_WARNING = "Daily bar close on the current trading date may represent intraday last price, not official close."


def _meta(symbol: str, status: str, **overrides):
    base = {
        "tool_name": "get_market_data",
        "raw_input": symbol,
        "normalized_symbol": symbol,
        "market": "a_share",
        "asset_type": "equity",
        "provider": "tencent",
        "requested_at": "2026-07-07T11:10:00+08:00",
        "latest_data_date": "2026-07-07",
        "latest_data_timestamp": "2026-07-07T00:00:00",
        "freshness_status": status,
        "is_intraday_like": False,
        "is_official_close": None,
        "row_count": 1,
        "source_success": True,
        "source_error": None,
        "warnings": [],
    }
    base.update(overrides)
    return base


class ReportGateTests(unittest.TestCase):
    def test_non_time_sensitive_stale_does_not_block(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请做 600519.SH 的长期历史概览",
            {"600519.SH": _meta("600519.SH", "stale", latest_data_date="2026-07-06")},
        )

        self.assertFalse(gate["blocked"])

    def test_time_sensitive_fresh_does_not_block(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请分析 600519.SH 今日表现",
            {"600519.SH": _meta("600519.SH", "fresh")},
        )

        self.assertFalse(gate["blocked"])

    def test_time_sensitive_stale_blocks(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请分析 600519.SH 今天盘中表现",
            {"600519.SH": _meta("600519.SH", "stale", latest_data_date="2026-07-06")},
        )

        self.assertTrue(gate["blocked"])
        self.assertIn("600519.SH", gate["symbols"])

    def test_time_sensitive_missing_blocks(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请给出 AAPL.US 最新走势",
            {"AAPL.US": _meta("AAPL.US", "missing", row_count=0, source_success=False)},
        )

        self.assertTrue(gate["blocked"])
        self.assertIn("missing", gate["blocking_statuses"])

    def test_time_sensitive_unknown_blocks(self) -> None:
        gate = evaluate_market_data_report_gate(
            "SPY.US current price change?",
            {"SPY.US": _meta("SPY.US", "unknown", latest_data_date=None, latest_data_timestamp=None)},
        )

        self.assertTrue(gate["blocked"])
        self.assertIn("unknown", gate["blocking_statuses"])

    def test_no_data_quality_does_not_block_in_mvp(self) -> None:
        gate = evaluate_market_data_report_gate("请分析 600519.SH 今日走势", None)

        self.assertFalse(gate["blocked"])
        self.assertIn("No get_market_data", gate["warnings"][0])

    def test_multi_symbol_one_stale_blocks_whole_report(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请分析 600519.SH 和 300750.SZ 今日表现",
            {
                "600519.SH": _meta("600519.SH", "fresh"),
                "300750.SZ": _meta("300750.SZ", "stale", latest_data_date="2026-07-06"),
            },
        )

        self.assertTrue(gate["blocked"])
        self.assertEqual(gate["symbols"], ["300750.SZ"])

    def test_closing_price_with_unofficial_close_warning_blocks(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请告诉我 600519.SH 今天收盘价",
            {"600519.SH": _meta("600519.SH", "fresh", warnings=[OFFICIAL_CLOSE_WARNING])},
        )

        self.assertTrue(gate["blocked"])
        self.assertIn("fresh_with_unofficial_close_warning", gate["blocking_statuses"])

    def test_intraday_with_unofficial_close_warning_does_not_block(self) -> None:
        gate = evaluate_market_data_report_gate(
            "请分析 600519.SH 盘中表现",
            {"600519.SH": _meta("600519.SH", "fresh", warnings=[OFFICIAL_CLOSE_WARNING])},
        )

        self.assertFalse(gate["blocked"])
        self.assertTrue(gate["warnings"])

    def test_data_insufficient_report_has_no_invented_market_numbers(self) -> None:
        quality = {"600519.SH": _meta("600519.SH", "stale", latest_data_date="2026-07-06")}
        gate = evaluate_market_data_report_gate("请分析 600519.SH 今日涨跌幅和成交额", quality)
        report = format_data_insufficient_report(gate, quality)

        self.assertIn("# Data Insufficient Report", report)
        self.assertNotIn("涨跌幅为", report)
        self.assertNotIn("成交额为", report)
        self.assertNotIn("截至 11:10", report)

    def test_data_insufficient_report_contains_source_summary(self) -> None:
        quality = {"600519.SH": _meta("600519.SH", "missing", row_count=0)}
        gate = evaluate_market_data_report_gate("请分析 600519.SH 今日走势", quality)
        report = format_data_insufficient_report(gate, quality)

        self.assertIn("## Data Source Summary", report)
        self.assertIn("## Missing or Unreliable Data", report)

    def test_english_time_sensitive_prompt_detected(self) -> None:
        detected = detect_time_sensitive_request("Analyze AAPL latest intraday volume")

        self.assertTrue(detected["is_time_sensitive"])
        self.assertIn("latest", detected["matched_terms"])

    def test_normal_path_still_appends_source_summary(self) -> None:
        original = "## Historical overview\nNo current-day claim."
        quality = {"600519.SH": _meta("600519.SH", "fresh")}
        gate = evaluate_market_data_report_gate("请做 600519.SH 的长期历史概览", quality)
        final = append_data_source_summary(original, quality)

        self.assertFalse(gate["blocked"])
        self.assertTrue(final.startswith(original))
        self.assertIn("## Data Source Summary", final)


if __name__ == "__main__":
    unittest.main()
