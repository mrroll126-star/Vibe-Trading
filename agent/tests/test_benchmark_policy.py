from __future__ import annotations

import unittest

from src.symbols.benchmark_policy import evaluate_market_wide_benchmark_intent


class BenchmarkPolicyTests(unittest.TestCase):
    def _policy(self, prompt: str, tool_name: str | None = "get_market_data", tool_args: dict | None = None) -> dict:
        return evaluate_market_wide_benchmark_intent(prompt, tool_name, tool_args or {})

    @staticmethod
    def _symbols(result: dict) -> set[str]:
        return {item["symbol"] for item in result["benchmarks"]}

    def assertDecision(self, result: dict, decision: str, market: str | None = None) -> None:
        self.assertEqual(result["decision"], decision)
        self.assertEqual(result["market"], market)
        self.assertTrue(result["metadata"]["benchmark_policy"])

    def test_a_share_today_allows_cn_benchmarks(self) -> None:
        result = self._policy("A股今天怎么样")
        self.assertDecision(result, "allow_benchmark", "cn")
        self.assertIn("000001.SH", self._symbols(result))
        self.assertIn("000300.SH", self._symbols(result))

    def test_hushen_market_allows_cn_benchmarks(self) -> None:
        result = self._policy("今天沪深市场表现如何")
        self.assertDecision(result, "allow_benchmark", "cn")

    def test_china_market_risk_allows_cn_benchmarks(self) -> None:
        result = self._policy("中国股市有什么风险")
        self.assertDecision(result, "allow_benchmark", "cn")

    def test_us_market_chinese_allows_us_benchmarks(self) -> None:
        result = self._policy("美股今天怎么样")
        self.assertDecision(result, "allow_benchmark", "us")
        self.assertIn("SPY.US", self._symbols(result))
        self.assertIn("QQQ.US", self._symbols(result))

    def test_us_market_english_allows_us_benchmarks(self) -> None:
        result = self._policy("US market today")
        self.assertDecision(result, "allow_benchmark", "us")

    def test_nasdaq_tech_overall_allows_qqq(self) -> None:
        result = self._policy("Nasdaq tech stocks overall risk")
        self.assertDecision(result, "allow_benchmark", "us")
        self.assertIn("QQQ.US", self._symbols(result))

    def test_hk_market_chinese_allows_hk_benchmarks(self) -> None:
        result = self._policy("港股今天怎么样")
        self.assertDecision(result, "allow_benchmark", "hk")
        self.assertIn("02800.HK", self._symbols(result))

    def test_hk_market_english_allows_hk_benchmarks(self) -> None:
        result = self._policy("Hong Kong market risk")
        self.assertDecision(result, "allow_benchmark", "hk")

    def test_global_stock_news_no_symbol_sets_metadata(self) -> None:
        result = self._policy("全市场新闻", "get_stock_news", {"scope": "global", "limit": 10})
        self.assertDecision(result, "not_market_wide", None)
        self.assertTrue(result["metadata"]["no_symbol_global_tool_allowed"])

    def test_sector_ranking_no_symbol_sets_metadata(self) -> None:
        result = self._policy("板块排行", "get_sector_info", {"mode": "ranking", "limit": 20})
        self.assertDecision(result, "not_market_wide", None)
        self.assertTrue(result["metadata"]["sector_ranking_no_symbol_allowed"])

    def test_ambiguous_market_prompt_asks_for_confirmation(self) -> None:
        result = self._policy("看看市场")
        self.assertDecision(result, "ask_for_confirmation", None)

    def test_recent_how_is_ambiguous(self) -> None:
        result = self._policy("最近怎么样")
        self.assertDecision(result, "ask_for_confirmation", None)

    def test_opportunity_prompt_is_ambiguous(self) -> None:
        result = self._policy("有什么机会")
        self.assertDecision(result, "ask_for_confirmation", None)

    def test_market_update_without_market_is_ambiguous(self) -> None:
        result = self._policy("market update")
        self.assertDecision(result, "ask_for_confirmation", None)

    def test_chinese_single_target_is_not_market_wide(self) -> None:
        result = self._policy("贵州茅台今天怎么样")
        self.assertDecision(result, "not_market_wide", None)
        self.assertEqual(result["reason"], "user_specified_target_intent")

    def test_explicit_symbol_is_not_market_wide(self) -> None:
        result = self._policy("600519.SH 今天怎么样")
        self.assertDecision(result, "not_market_wide", None)

    def test_bare_numeric_symbol_is_not_market_wide(self) -> None:
        result = self._policy("000001 今天怎么样")
        self.assertDecision(result, "not_market_wide", None)

    def test_explicit_us_symbol_is_not_market_wide(self) -> None:
        result = self._policy("QQQ.US 最近怎么样")
        self.assertDecision(result, "not_market_wide", None)

    def test_tencent_name_is_not_market_wide(self) -> None:
        result = self._policy("腾讯最近怎么样")
        self.assertDecision(result, "not_market_wide", None)

    def test_company_specific_tool_blocks_market_benchmark_policy(self) -> None:
        result = self._policy("A股今天怎么样", "get_financial_statements", {"code": "000001.SH"})
        self.assertDecision(result, "block", "cn")
        self.assertIn("does not bypass asset-type routing", result["warnings"][0])

    def test_us_tech_market_allows_benchmark(self) -> None:
        result = self._policy("美股科技股怎么样", "get_market_data", {"symbol": "QQQ.US"})
        self.assertDecision(result, "allow_benchmark", "us")
        self.assertEqual(self._symbols(result), {"QQQ.US"})

    def test_us_tech_market_rejects_single_stock_outside_benchmarks(self) -> None:
        result = self._policy("美股科技股怎么样", "get_market_data", {"symbol": "AAPL.US"})
        self.assertDecision(result, "block", "us")
        self.assertIn("AAPL.US", result["metadata"]["rejected_symbols"])

    def test_a_share_market_rejects_stock_outside_benchmarks(self) -> None:
        result = self._policy("A股今天怎么样", "get_market_data", {"symbol": "600519.SH"})
        self.assertDecision(result, "block", "cn")
        self.assertIn("600519.SH", result["metadata"]["rejected_symbols"])

    def test_a_share_market_allows_000001_benchmark(self) -> None:
        result = self._policy("A股今天怎么样", "get_market_data", {"symbol": "000001.SH"})
        self.assertDecision(result, "allow_benchmark", "cn")
        self.assertEqual(self._symbols(result), {"000001.SH"})

    def test_a_share_market_allows_399001_benchmark(self) -> None:
        result = self._policy("A股今天怎么样", "get_market_data", {"symbol": "399001.SZ"})
        self.assertDecision(result, "allow_benchmark", "cn")
        self.assertEqual(self._symbols(result), {"399001.SZ"})


if __name__ == "__main__":
    unittest.main()

