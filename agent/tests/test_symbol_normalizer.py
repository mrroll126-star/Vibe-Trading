from __future__ import annotations

import unittest

from src.symbols import normalize_many, normalize_symbol


class SymbolNormalizerTests(unittest.TestCase):
    def test_us_symbols(self) -> None:
        cases = [
            ("QQQ", "QQQ.US", "etf"),
            ("SPY", "SPY.US", "etf"),
            ("AAPL", "AAPL.US", "stock"),
            ("NVDA", "NVDA.US", "stock"),
            ("QQQ.US", "QQQ.US", "etf"),
        ]
        for raw, expected, asset_type in cases:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw)
                self.assertEqual(result.normalized_symbol, expected)
                self.assertEqual(result.market, "US")
                self.assertEqual(result.exchange, "US")
                self.assertEqual(result.asset_type, asset_type)
                self.assertTrue(result.is_valid)

    def test_us_letter_ticker_too_long_is_invalid(self) -> None:
        result = normalize_symbol("ABCDEFG")
        self.assertIsNone(result.normalized_symbol)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.warnings)

    def test_a_share_symbols(self) -> None:
        cases = [
            ("600519", "600519.SH", "stock"),
            ("300750", "300750.SZ", "stock"),
            ("601318", "601318.SH", "stock"),
            ("510300", "510300.SH", "etf"),
            ("159915", "159915.SZ", "etf"),
            ("600519.SH", "600519.SH", "stock"),
            ("SH600519", "600519.SH", "stock"),
            ("sh.600519", "600519.SH", "stock"),
            ("300750.SZ", "300750.SZ", "stock"),
            ("SZ300750", "300750.SZ", "stock"),
            ("sz.300750", "300750.SZ", "stock"),
        ]
        for raw, expected, asset_type in cases:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw)
                self.assertEqual(result.normalized_symbol, expected)
                self.assertEqual(result.market, "CN")
                self.assertEqual(result.exchange, expected.rsplit(".", 1)[1])
                self.assertEqual(result.asset_type, asset_type)

    def test_ambiguous_000001_defaults_to_stock_with_warning(self) -> None:
        result = normalize_symbol("000001")
        self.assertEqual(result.normalized_symbol, "000001.SZ")
        self.assertEqual(result.market, "CN")
        self.assertEqual(result.exchange, "SZ")
        self.assertEqual(result.asset_type, "stock")
        self.assertTrue(result.needs_confirmation)
        self.assertTrue(result.warnings)

    def test_000001_can_prefer_index(self) -> None:
        for context in [{"prefer_index": True}, {"market": "index"}]:
            with self.subTest(context=context):
                result = normalize_symbol("000001", context=context)
                self.assertEqual(result.normalized_symbol, "000001.SH")
                self.assertEqual(result.market, "CN")
                self.assertEqual(result.exchange, "SH")
                self.assertEqual(result.asset_type, "index")
                self.assertTrue(result.needs_confirmation)
                self.assertTrue(result.warnings)

    def test_hk_symbols(self) -> None:
        cases = [
            ("700", {"market": "HK"}, "00700.HK"),
            ("0700", {"market": "HK"}, "00700.HK"),
            ("00700", None, "00700.HK"),
            ("9988", {"market": "HK"}, "09988.HK"),
            ("09988", None, "09988.HK"),
            ("00700.HK", None, "00700.HK"),
            ("HK.00700", None, "00700.HK"),
        ]
        for raw, context, expected in cases:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw, context=context)
                self.assertEqual(result.normalized_symbol, expected)
                self.assertEqual(result.market, "HK")
                self.assertEqual(result.exchange, "HK")
                self.assertEqual(result.asset_type, "stock")

    def test_chinese_names_are_deferred(self) -> None:
        for raw in ["贵州茅台", "腾讯"]:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw)
                self.assertIsNone(result.normalized_symbol)
                self.assertTrue(result.needs_confirmation)
                self.assertEqual(result.name, raw)
                self.assertTrue(result.warnings)

    def test_empty_input_is_invalid(self) -> None:
        for raw in ["", "   "]:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw)
                self.assertIsNone(result.normalized_symbol)
                self.assertFalse(result.is_valid)
                self.assertTrue(result.warnings)

    def test_short_numeric_without_context_is_hk_candidate(self) -> None:
        result = normalize_symbol("123")
        self.assertIsNone(result.normalized_symbol)
        self.assertTrue(result.needs_confirmation)
        self.assertEqual(result.candidate_symbols, ["00123.HK"])
        self.assertTrue(result.warnings)

    def test_short_numeric_with_hk_context_is_hk_symbol(self) -> None:
        result = normalize_symbol("123", context={"market": "HK"})
        self.assertEqual(result.normalized_symbol, "00123.HK")
        self.assertEqual(result.market, "HK")
        self.assertFalse(result.needs_confirmation)

    def test_invalid_mixed_input(self) -> None:
        for raw in ["AAPL123", "12AB", "600519.XY"]:
            with self.subTest(raw=raw):
                result = normalize_symbol(raw)
                self.assertIsNone(result.normalized_symbol)
                self.assertTrue(result.warnings)

    def test_result_to_dict_and_normalize_many(self) -> None:
        one = normalize_symbol("SPY")
        self.assertEqual(one.to_dict()["normalized_symbol"], "SPY.US")

        many = normalize_many(["SPY", "600519"])
        self.assertEqual([item.normalized_symbol for item in many], ["SPY.US", "600519.SH"])


if __name__ == "__main__":
    unittest.main()
