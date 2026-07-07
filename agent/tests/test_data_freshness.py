from __future__ import annotations

import json
import unittest
from datetime import datetime

import pandas as pd

from src.data_quality import assess_freshness
from src.market_data import fetch_market_data_json


REQUESTED_AT = datetime(2026, 7, 7, 11, 10, 0)


class FreshnessMetadataTests(unittest.TestCase):
    def test_empty_data_is_missing(self) -> None:
        meta = assess_freshness(
            [],
            tool_name="get_market_data",
            raw_input="600519.SH",
            normalized_symbol="600519.SH",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")
        self.assertEqual(meta["row_count"], 0)
        self.assertFalse(meta["source_success"])

    def test_rows_without_date_are_unknown(self) -> None:
        meta = assess_freshness(
            [{"close": 10.0}],
            tool_name="get_market_data",
            raw_input="AAPL.US",
            normalized_symbol="AAPL.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "unknown")
        self.assertEqual(meta["row_count"], 1)
        self.assertTrue(meta["source_success"])

    def test_yesterday_latest_is_stale_when_time_sensitive(self) -> None:
        meta = assess_freshness(
            [{"trade_date": "2026-07-06", "close": 100.0}],
            tool_name="get_market_data",
            raw_input="SPY.US",
            normalized_symbol="SPY.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "stale")
        self.assertEqual(meta["latest_data_date"], "2026-07-06")

    def test_today_latest_is_fresh(self) -> None:
        meta = assess_freshness(
            [{"trade_date": "2026-07-07T10:30:00", "price": 100.0}],
            tool_name="get_market_data",
            raw_input="SPY.US",
            normalized_symbol="SPY.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
            interval="1m",
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "fresh")
        self.assertEqual(meta["latest_data_date"], "2026-07-07")

    def test_today_daily_close_gets_intraday_warning(self) -> None:
        meta = assess_freshness(
            [{"trade_date": "2026-07-07", "close": 100.0}],
            tool_name="get_market_data",
            raw_input="600519.SH",
            normalized_symbol="600519.SH",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
            interval="1D",
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "fresh")
        self.assertTrue(meta["is_intraday_like"])
        self.assertFalse(meta["is_official_close"])
        self.assertTrue(any("not official close" in warning for warning in meta["warnings"]))

    def test_ok_false_is_missing_with_source_error(self) -> None:
        meta = assess_freshness(
            {"ok": False, "error": "auth failed"},
            tool_name="get_market_data",
            raw_input="AAPL.US",
            normalized_symbol="AAPL.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(meta["freshness_status"], "missing")
        self.assertEqual(meta["source_error"], "auth failed")
        self.assertFalse(meta["source_success"])

    def test_extracts_dates_from_dataframe_list_and_dict(self) -> None:
        df = pd.DataFrame({"close": [1.0]}, index=pd.to_datetime(["2026-07-07"]))
        df.index.name = "trade_date"

        dataframe_meta = assess_freshness(
            df,
            tool_name="get_market_data",
            raw_input="AAPL.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()
        list_meta = assess_freshness(
            [{"date": "20260707", "close": 1.0}],
            tool_name="get_market_data",
            raw_input="AAPL.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()
        dict_meta = assess_freshness(
            {"timestamp": "2026-07-07T09:30:00", "close": 1.0},
            tool_name="get_market_data",
            raw_input="AAPL.US",
            requested_at=REQUESTED_AT,
            time_sensitive=True,
        ).to_dict()

        self.assertEqual(dataframe_meta["latest_data_date"], "2026-07-07")
        self.assertEqual(list_meta["latest_data_date"], "2026-07-07")
        self.assertEqual(dict_meta["latest_data_date"], "2026-07-07")

    def test_get_market_data_wrapper_keeps_original_data(self) -> None:
        class _Loader:
            def fetch(self, codes, start_date, end_date, interval="1D"):
                df = pd.DataFrame(
                    {"close": [10.0, 11.0]},
                    index=pd.to_datetime(["2026-07-06", "2026-07-07"]),
                )
                df.index.name = "trade_date"
                return {codes[0]: df}

        payload = fetch_market_data_json(
            codes=["SPY.US"],
            start_date="2026-07-06",
            end_date="2026-07-07",
            source="yahoo",
            loader_resolver=lambda source: _Loader,
        )
        parsed = json.loads(payload)

        self.assertIsInstance(parsed["SPY.US"], list)
        self.assertEqual(parsed["SPY.US"][0]["close"], 10.0)
        self.assertIn("_data_quality", parsed)
        self.assertIn("SPY.US", parsed["_data_quality"])


if __name__ == "__main__":
    unittest.main()
