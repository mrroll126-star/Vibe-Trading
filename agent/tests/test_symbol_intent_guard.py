from __future__ import annotations

import unittest

from src.symbols.intent_guard import evaluate_symbol_intent_guard


class SymbolIntentGuardTests(unittest.TestCase):
    def _guard(self, prompt: str, symbol, tool_name: str = "get_market_data") -> dict:
        return evaluate_symbol_intent_guard(
            original_prompt=prompt,
            tool_name=tool_name,
            tool_args={"codes": symbol},
        )

    def assertDecision(self, result: dict, decision: str, reason: str | None = None) -> None:
        self.assertEqual(result["decision"], decision)
        if reason is not None:
            self.assertEqual(result["reason"], reason)

    def test_safe_a_share_bare_symbol_allows(self) -> None:
        result = self._guard("请分析 600519 今天表现", ["600519.SH"])
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")
        self.assertEqual(result["metadata"]["source"], "normalizer")

    def test_safe_us_bare_symbol_allows(self) -> None:
        result = self._guard("Analyze QQQ recent performance", ["QQQ.US"])
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_safe_hk_bare_symbol_allows(self) -> None:
        result = self._guard("请分析 00700 最近表现", ["00700.HK"])
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_safe_hk_four_digit_bare_symbol_allows(self) -> None:
        result = self._guard("请分析 9988 最近表现", ["09988.HK"])
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_ambiguous_000001_to_sz_clarifies(self) -> None:
        result = self._guard("请分析 000001 今天表现", ["000001.SZ"])
        self.assertDecision(result, "clarify", "ambiguous_000001_requires_confirmation")

    def test_ambiguous_000001_to_sh_clarifies(self) -> None:
        result = self._guard("请分析 000001 今天表现", ["000001.SH"])
        self.assertDecision(result, "clarify", "ambiguous_000001_requires_confirmation")

    def test_explicit_000001_sz_allows(self) -> None:
        result = self._guard("请分析 000001.SZ 今天表现", ["000001.SZ"])
        self.assertDecision(result, "allow", "explicit_symbol_match")

    def test_explicit_000001_sh_allows(self) -> None:
        result = self._guard("请分析 000001.SH 今天表现", ["000001.SH"])
        self.assertDecision(result, "allow", "explicit_symbol_match")

    def test_chinese_name_guizhou_maotai_clarifies(self) -> None:
        result = self._guard("请分析 贵州茅台 今天表现", ["600519.SH"])
        self.assertDecision(result, "clarify", "chinese_name_requires_confirmation")

    def test_chinese_name_ping_an_bank_clarifies(self) -> None:
        result = self._guard("请分析 平安银行 今天表现", ["000001.SZ"])
        self.assertDecision(result, "clarify", "chinese_name_requires_confirmation")

    def test_chinese_name_apple_clarifies(self) -> None:
        result = self._guard("请分析 苹果公司 最近表现", ["AAPL.US"])
        self.assertDecision(result, "clarify", "chinese_name_requires_confirmation")

    def test_explicit_a_share_mismatch_blocks(self) -> None:
        result = self._guard("请分析 600519.SH 今天表现", ["300750.SZ"])
        self.assertDecision(result, "block", "tool_symbol_mismatch")

    def test_explicit_us_mismatch_blocks(self) -> None:
        result = self._guard("Analyze QQQ.US", ["SPY.US"])
        self.assertDecision(result, "block", "tool_symbol_mismatch")

    def test_no_symbol_prompt_blocks_untraceable_tool_symbol(self) -> None:
        result = self._guard("请分析今天市场", ["600519.SH"])
        self.assertDecision(result, "block", "tool_symbol_not_traceable_to_user_prompt")

    def test_non_market_data_tool_allows(self) -> None:
        result = self._guard("请分析 600519", ["600519.SH"], tool_name="web_search")
        self.assertDecision(result, "allow", "unsupported_tool_for_mvp")
        self.assertEqual(result["metadata"]["source"], "unsupported_tool")

    def test_missing_get_market_data_symbol_blocks(self) -> None:
        result = evaluate_symbol_intent_guard("请分析 600519", "get_market_data", {})
        self.assertDecision(result, "block", "missing_or_untraceable_tool_symbol")

    def test_multiple_symbols_one_ambiguous_clarifies(self) -> None:
        result = self._guard("请分析 600519 和 000001", ["600519.SH", "000001.SZ"])
        self.assertDecision(result, "clarify", "ambiguous_000001_requires_confirmation")
        self.assertEqual(len(result["details"]), 2)

    def test_multiple_symbols_both_safe_allow(self) -> None:
        result = self._guard("请分析 600519 和 QQQ", ["600519.SH", "QQQ.US"])
        self.assertDecision(result, "allow")
        self.assertEqual(len(result["details"]), 2)

    def test_symbol_extraction_supports_code_key(self) -> None:
        result = evaluate_symbol_intent_guard("请分析 600519", "get_market_data", {"code": "600519.SH"})
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_symbol_extraction_supports_comma_separated_symbols(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 600519 和 QQQ",
            "get_market_data",
            {"symbols": "600519.SH,QQQ.US"},
        )
        self.assertDecision(result, "allow")

    def test_get_fund_flow_ambiguous_000001_clarifies(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 000001 今天表现",
            "get_fund_flow",
            {"codes": ["000001.SZ"]},
        )
        self.assertDecision(result, "clarify", "ambiguous_000001_requires_confirmation")
        self.assertTrue(result["metadata"]["guarded_tool"])
        self.assertEqual(result["metadata"]["guarded_tool_group"], "stock_specific")

    def test_get_stock_news_chinese_name_clarifies(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 贵州茅台 今天表现",
            "get_stock_news",
            {"code": "600519.SH"},
        )
        self.assertDecision(result, "clarify", "chinese_name_requires_confirmation")

    def test_get_research_reports_safe_a_share_allows(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 600519",
            "get_research_reports",
            {"code": "600519.SH"},
        )
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_get_sector_info_safe_us_allows(self) -> None:
        result = evaluate_symbol_intent_guard(
            "Analyze QQQ",
            "get_sector_info",
            {"code": "QQQ.US"},
        )
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")

    def test_web_search_with_symbol_query_is_not_guarded(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 000001",
            "web_search",
            {"query": "000001.SZ"},
        )
        self.assertDecision(result, "allow", "unsupported_tool_for_mvp")
        self.assertFalse(result["metadata"]["guarded_tool"])

    def test_search_symbol_chinese_name_is_not_guarded(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 贵州茅台",
            "search_symbol",
            {"query": "贵州茅台"},
        )
        self.assertDecision(result, "allow", "unsupported_tool_for_mvp")
        self.assertFalse(result["metadata"]["guarded_tool"])

    def test_get_fund_flow_explicit_mismatch_blocks(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 600519.SH",
            "get_fund_flow",
            {"codes": ["300750.SZ"]},
        )
        self.assertDecision(result, "block", "tool_symbol_mismatch")

    def test_get_stock_news_no_symbol_prompt_blocks(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析今天市场",
            "get_stock_news",
            {"code": "600519.SH"},
        )
        self.assertDecision(result, "block", "tool_symbol_not_traceable_to_user_prompt")

    def test_query_field_extracts_standard_symbol_for_guarded_tool(self) -> None:
        result = evaluate_symbol_intent_guard(
            "请分析 600519",
            "get_sector_info",
            {"query": "请查询 600519.SH 所属板块"},
        )
        self.assertDecision(result, "allow", "safe_bare_symbol_mapping")


if __name__ == "__main__":
    unittest.main()
