from __future__ import annotations

import unittest

from src.data_quality import append_data_source_summary, format_data_source_summary


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


class DataSourceSummaryTests(unittest.TestCase):
    def test_fresh_summary_displays_fresh(self) -> None:
        summary = format_data_source_summary({"600519.SH": _meta("600519.SH", "fresh")})

        self.assertIn("## Data Source Summary", summary)
        self.assertIn("600519.SH", summary)
        self.assertIn("fresh", summary)
        self.assertNotIn("## Missing Data", summary)

    def test_stale_summary_displays_missing_note(self) -> None:
        summary = format_data_source_summary(
            {
                "600519.SH": _meta(
                    "600519.SH",
                    "stale",
                    latest_data_date="2026-07-06",
                    warnings=["Latest data date 2026-07-06 is older than requested date 2026-07-07."],
                )
            }
        )

        self.assertIn("stale", summary)
        self.assertIn("## Missing Data", summary)
        self.assertIn("do not treat this as today's, intraday, latest, or realtime market fact", summary)

    def test_missing_summary_displays_missing(self) -> None:
        summary = format_data_source_summary(
            {
                "AAPL.US": _meta(
                    "AAPL.US",
                    "missing",
                    row_count=0,
                    source_success=False,
                    source_error="No rows returned by data source.",
                )
            }
        )

        self.assertIn("missing", summary)
        self.assertIn("No rows returned by data source.", summary)
        self.assertIn("no usable market-data rows were returned", summary)

    def test_unknown_summary_displays_unknown(self) -> None:
        summary = format_data_source_summary(
            {
                "SPY.US": _meta(
                    "SPY.US",
                    "unknown",
                    latest_data_date=None,
                    latest_data_timestamp=None,
                )
            }
        )

        self.assertIn("unknown", summary)
        self.assertIn("timestamp", summary)

    def test_current_day_daily_close_warning_is_displayed(self) -> None:
        warning = "Daily bar close on the current trading date may represent intraday last price, not official close."
        summary = format_data_source_summary(
            {"600519.SH": _meta("600519.SH", "fresh", warnings=[warning], is_intraday_like=True, is_official_close=False)}
        )

        self.assertIn("## Source Warnings", summary)
        self.assertIn(warning, summary)

    def test_no_data_quality_is_noop(self) -> None:
        self.assertEqual(format_data_source_summary(None), "")
        self.assertEqual(append_data_source_summary("原始报告正文", None), "原始报告正文")

    def test_multiple_symbols_are_displayed(self) -> None:
        summary = format_data_source_summary(
            {
                "600519.SH": _meta("600519.SH", "fresh"),
                "300750.SZ": _meta("300750.SZ", "stale", latest_data_date="2026-07-06"),
            }
        )

        self.assertIn("600519.SH", summary)
        self.assertIn("300750.SZ", summary)

    def test_append_does_not_change_original_body(self) -> None:
        original = "## 原始分析\n正文内容。"
        appended = append_data_source_summary(original, {"600519.SH": _meta("600519.SH", "fresh")})

        self.assertTrue(appended.startswith(original))
        self.assertIn("## Data Source Summary", appended)


if __name__ == "__main__":
    unittest.main()
