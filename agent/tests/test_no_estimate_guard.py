from __future__ import annotations

import unittest

from src.data_quality import (
    append_no_estimate_warning,
    detect_no_estimate_request,
    find_estimated_market_fact_claims,
)


class NoEstimateGuardTests(unittest.TestCase):
    def test_chinese_do_not_estimate_is_detected(self) -> None:
        detected = detect_no_estimate_request("请分析 600519.SH，不要估算。")

        self.assertTrue(detected["enabled"])
        self.assertIn("不要估算", detected["matched_terms"])

    def test_retrieved_data_only_is_detected(self) -> None:
        detected = detect_no_estimate_request("只使用实际获取到的数据，没有拿到就说没有。")

        self.assertTrue(detected["enabled"])

    def test_english_do_not_estimate_is_detected(self) -> None:
        detected = detect_no_estimate_request("Analyze AAPL, do not estimate.")

        self.assertTrue(detected["enabled"])

    def test_turnover_estimate_claim_is_flagged(self) -> None:
        claims = find_estimated_market_fact_claims("成交额估算约 32.7 亿元。")

        self.assertEqual(len(claims), 1)
        self.assertIn("成交额", claims[0])

    def test_price_change_estimate_claim_is_flagged(self) -> None:
        claims = find_estimated_market_fact_claims("涨跌幅（估算）-1.50%。")

        self.assertEqual(len(claims), 1)
        self.assertIn("涨跌幅", claims[0])

    def test_interpretive_maybe_without_market_number_is_not_flagged(self) -> None:
        claims = find_estimated_market_fact_claims("可能受行业情绪影响。")

        self.assertEqual(claims, [])

    def test_no_prompt_requirement_does_not_append_warning(self) -> None:
        report = "成交额估算约 32.7 亿元。"
        final = append_no_estimate_warning(report, "请分析 600519.SH 今日表现")

        self.assertEqual(final, report)

    def test_no_estimate_prompt_appends_warning(self) -> None:
        report = "成交额估算约 32.7 亿元。"
        final = append_no_estimate_warning(report, "请分析 600519.SH，不要估算")

        self.assertIn("## No Estimate Warning", final)
        self.assertIn("成交额估算约 32.7 亿元", final)


if __name__ == "__main__":
    unittest.main()
