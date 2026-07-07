from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import pandas as pd

from src.market_data import fetch_market_data
from src.symbols.config import is_symbol_normalizer_enabled


class _LoaderRecorder:
    calls: list[tuple[list[str], str, str, str]] = []

    def fetch(self, codes, start_date, end_date, interval="1D"):
        self.__class__.calls.append((list(codes), start_date, end_date, interval))
        out = {}
        for code in codes:
            df = pd.DataFrame(
                {"close": [10.0]},
                index=pd.to_datetime([end_date]),
            )
            df.index.name = "trade_date"
            out[code] = df
        return out


def _loader_resolver(_source: str):
    return _LoaderRecorder


def _reset_loader_calls() -> None:
    _LoaderRecorder.calls = []


class MarketDataSymbolNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        _reset_loader_calls()

    def test_feature_flag_helper_defaults_off(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_symbol_normalizer_enabled())
        for value in ("1", "true", "True", "yes", "on"):
            with self.subTest(value=value), patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": value}):
                self.assertTrue(is_symbol_normalizer_enabled())
        for value in ("0", "false", "off", "no", "anything"):
            with self.subTest(value=value), patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": value}):
                self.assertFalse(is_symbol_normalizer_enabled())

    def test_flag_off_does_not_normalize_bare_a_share(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "0"}):
            out = fetch_market_data(
                codes=["600519"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertIn("600519", out)
        self.assertNotIn("600519.SH", out)
        self.assertNotIn("_symbol_normalization", out)
        self.assertEqual(_LoaderRecorder.calls[0][0], ["600519"])

    def test_flag_off_does_not_normalize_bare_us_symbol(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "false"}):
            out = fetch_market_data(
                codes=["QQQ"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertIn("QQQ", out)
        self.assertNotIn("QQQ.US", out)
        self.assertNotIn("_symbol_normalization", out)

    def test_flag_off_explicit_symbol_behavior_unchanged(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": ""}):
            out = fetch_market_data(
                codes=["SPY.US"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertIn("SPY.US", out)
        self.assertIn("SPY.US", out["_data_quality"])
        self.assertEqual(out["_data_quality"]["SPY.US"]["raw_input"], "SPY.US")

    def test_flag_on_normalizes_a_share_and_etf_symbols(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "1"}):
            out = fetch_market_data(
                codes=["600519", "300750", "510300", "159915"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        for expected in ("600519.SH", "300750.SZ", "510300.SH", "159915.SZ"):
            self.assertIn(expected, out)
            self.assertIn(expected, out["_data_quality"])
        self.assertEqual(out["_symbol_normalization"]["600519"]["normalized_symbol"], "600519.SH")
        self.assertEqual(out["_symbol_normalization"]["510300"]["asset_type"], "etf")
        self.assertEqual(out["_data_quality"]["600519.SH"]["raw_input"], "600519")

    def test_flag_on_normalizes_us_and_hk_symbols(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "yes"}):
            out = fetch_market_data(
                codes=["QQQ", "SPY", "00700", "9988"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        for expected in ("QQQ.US", "SPY.US", "00700.HK", "09988.HK"):
            self.assertIn(expected, out)
        self.assertEqual(out["_symbol_normalization"]["9988"]["normalized_symbol"], "09988.HK")

    def test_flag_on_ambiguous_000001_returns_warning_without_provider_call(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "on"}):
            out = fetch_market_data(
                codes=["000001"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertEqual(_LoaderRecorder.calls, [])
        self.assertIn("000001", out["_unresolved"])
        meta = out["_symbol_normalization"]["000001"]
        self.assertEqual(meta["normalized_symbol"], "000001.SZ")
        self.assertTrue(meta["needs_confirmation"])
        self.assertTrue(meta["warnings"])

    def test_flag_on_chinese_name_requires_confirmation_without_provider_call(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "1"}):
            out = fetch_market_data(
                codes=["贵州茅台"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertEqual(_LoaderRecorder.calls, [])
        self.assertIn("贵州茅台", out["_unresolved"])
        self.assertTrue(out["_symbol_normalization"]["贵州茅台"]["needs_confirmation"])

    def test_flag_on_invalid_symbol_does_not_call_provider(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "1"}):
            out = fetch_market_data(
                codes=["AAPL123"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertEqual(_LoaderRecorder.calls, [])
        self.assertIn("AAPL123", out["_unresolved"])
        self.assertTrue(out["_symbol_normalization"]["AAPL123"]["warnings"])

    def test_flag_on_multi_symbol_has_metadata_and_data_quality(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "true"}):
            out = fetch_market_data(
                codes=["600519", "QQQ", "贵州茅台"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        self.assertIn("600519", out["_symbol_normalization"])
        self.assertIn("QQQ", out["_symbol_normalization"])
        self.assertIn("贵州茅台", out["_symbol_normalization"])
        self.assertIn("600519.SH", out["_data_quality"])
        self.assertIn("QQQ.US", out["_data_quality"])
        self.assertIn("贵州茅台", out["_data_quality"])

    def test_flag_on_explicit_standard_symbols_are_not_broken(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "1"}):
            out = fetch_market_data(
                codes=["600519.SH", "300750.SZ", "SPY.US", "00700.HK"],
                start_date="2026-07-07",
                end_date="2026-07-07",
                loader_resolver=_loader_resolver,
            )

        for expected in ("600519.SH", "300750.SZ", "SPY.US", "00700.HK"):
            self.assertIn(expected, out)
            self.assertIn(expected, out["_data_quality"])
        self.assertEqual(out["_symbol_normalization"]["SPY.US"]["normalized_symbol"], "SPY.US")


if __name__ == "__main__":
    unittest.main()
