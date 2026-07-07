from __future__ import annotations

import unittest
from datetime import datetime

from src.data_quality import (
    assess_fund_flow_quality,
    assess_research_reports_quality,
    assess_stock_news_quality,
    format_data_source_summary,
)


REQUESTED_AT = datetime(2026, 7, 7, 11, 10, 0)


class ExtendedDataQualityTests(unittest.TestCase):
    def test_fund_flow_ok_false_is_missing(self) -> None:
        meta = assess_fund_flow_quality(
            {"ok": False, "error": "upstream failed"},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")
        self.assertFalse(meta["source_success"])
        self.assertEqual(meta["source_error"], "upstream failed")

    def test_fund_flow_connection_aborted_error_is_missing(self) -> None:
        meta = assess_fund_flow_quality(
            {"symbol": "600519.SH", "error": "Connection aborted: RemoteDisconnected"},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")
        self.assertIn("Connection aborted", meta["source_error"])

    def test_fund_flow_data_with_date_is_fresh_or_stale(self) -> None:
        fresh = assess_fund_flow_quality(
            {"rows": [{"timestamp": "2026-07-07 10:30", "main": 1.0}]},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()
        stale = assess_fund_flow_quality(
            {"rows": [{"timestamp": "2026-07-06", "main": 1.0}]},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(fresh["freshness_status"], "fresh")
        self.assertEqual(stale["freshness_status"], "stale")

    def test_stock_news_empty_is_missing(self) -> None:
        meta = assess_stock_news_quality(
            {"ok": True, "data": {"articles": []}},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")

    def test_stock_news_older_than_three_days_is_stale(self) -> None:
        meta = assess_stock_news_quality(
            {"ok": True, "data": {"articles": [{"published": "2026-07-01 09:00:00"}]}},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "stale")
        self.assertTrue(any("outdated" in warning for warning in meta["warnings"]))

    def test_stock_news_no_date_is_unknown(self) -> None:
        meta = assess_stock_news_quality(
            {"ok": True, "data": {"articles": [{"title": "headline"}]}},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "unknown")

    def test_research_reports_error_is_missing(self) -> None:
        meta = assess_research_reports_quality(
            {"ok": False, "error": "HTTP 400"},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney+ths",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")
        self.assertEqual(meta["source_error"], "HTTP 400")

    def test_research_reports_old_date_warns(self) -> None:
        meta = assess_research_reports_quality(
            {"ok": True, "data": {"reports": [{"publish_date": "2026-01-01"}]}},
            raw_input="600519.SH",
            symbol="600519.SH",
            provider="eastmoney+ths",
            requested_at=REQUESTED_AT,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "fresh")
        self.assertTrue(any("old" in warning.lower() for warning in meta["warnings"]))

    def test_source_summary_displays_multiple_tool_groups_and_missing(self) -> None:
        quality = {
            "get_fund_flow:600519.SH": assess_fund_flow_quality(
                {"error": "Connection aborted"},
                raw_input="600519.SH",
                symbol="600519.SH",
                provider="eastmoney",
                requested_at=REQUESTED_AT,
            ).to_dict(),
            "get_stock_news:600519.SH": assess_stock_news_quality(
                {"ok": True, "data": {"articles": [{"published": "2026-07-01"}]}},
                raw_input="600519.SH",
                symbol="600519.SH",
                provider="eastmoney",
                requested_at=REQUESTED_AT,
            ).to_dict(),
        }

        summary = format_data_source_summary(quality)

        self.assertIn("### get_fund_flow", summary)
        self.assertIn("### get_stock_news", summary)
        self.assertIn("## Missing Data", summary)
        self.assertIn("Connection aborted", summary)
        self.assertIn("News may be outdated", summary)


if __name__ == "__main__":
    unittest.main()
