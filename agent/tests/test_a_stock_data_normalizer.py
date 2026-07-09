from __future__ import annotations

import unittest

from src.adapters.a_stock_data import normalize_a_stock_financials_result


class AStockDataFinancialNormalizerTests(unittest.TestCase):
    def test_report_date_rows_normalize_successfully(self) -> None:
        result = normalize_a_stock_financials_result(
            [{"report_date": "2026-03-31", "revenue": 100, "net_profit": 20}],
            "600519.SH",
            source="sina_financials",
            upstream="a-stock-data",
            statement_type="income",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "a_stock_data")
        self.assertEqual(result["source"], "sina_financials")
        self.assertEqual(result["upstream"], "a-stock-data")
        self.assertEqual(result["statement_type"], "income")
        self.assertEqual(result["data"]["600519.SH"][0]["report_date"], "2026-03-31")
        self.assertEqual(result["data"]["600519.SH"][0]["revenue"], 100)
        quality = result["_data_quality"]["600519.SH"]
        self.assertEqual(quality["freshness_status"], "unknown")
        self.assertEqual(quality["status"], "unknown")
        self.assertEqual(quality["latest_date"], "2026-03-31")
        self.assertEqual(quality["latest_data_date"], "2026-03-31")
        self.assertEqual(quality["row_count"], 1)
        self.assertTrue(quality["source_success"])

    def test_chinese_report_period_is_recognized(self) -> None:
        result = normalize_a_stock_financials_result(
            [{"报告期": "2025-12-31", "营业收入": "123.4", "净利润": "56.7"}],
            "300750.SZ",
        )

        row = result["data"]["300750.SZ"][0]
        self.assertTrue(result["ok"])
        self.assertEqual(row["report_date"], "2025-12-31")
        self.assertEqual(row["revenue"], "123.4")
        self.assertEqual(row["net_profit"], "56.7")

    def test_empty_list_is_missing(self) -> None:
        result = normalize_a_stock_financials_result([], "600519.SH")

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertEqual(quality["freshness_status"], "missing")
        self.assertEqual(quality["row_count"], 0)
        self.assertFalse(quality["source_success"])
        self.assertIn("no financial rows returned", quality["source_error"])

    def test_none_payload_is_missing(self) -> None:
        result = normalize_a_stock_financials_result(None, "600519.SH")

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertEqual(quality["freshness_status"], "missing")
        self.assertIn("empty raw financials payload", quality["errors"])

    def test_ok_false_payload_is_missing_with_error(self) -> None:
        result = normalize_a_stock_financials_result(
            {"ok": False, "error": "HTTP 500", "message": "upstream failed"},
            "600519.SH",
        )

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertEqual(quality["freshness_status"], "missing")
        self.assertIn("HTTP 500", quality["source_error"])
        self.assertIn("upstream failed", quality["source_error"])

    def test_rows_without_date_are_unknown_and_warn(self) -> None:
        result = normalize_a_stock_financials_result(
            [{"营业收入": 1000, "净利润": 100}],
            "600519.SH",
        )

        quality = result["_data_quality"]["600519.SH"]
        self.assertTrue(result["ok"])
        self.assertEqual(quality["freshness_status"], "unknown")
        self.assertIsNone(quality["latest_data_date"])
        self.assertIn("no_as_of_date", quality["warnings"])

    def test_dict_data_rows_are_extracted(self) -> None:
        result = normalize_a_stock_financials_result(
            {"ok": True, "data": [{"date": "2026-06-30", "total_assets": 10}]},
            "600519.SH",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["600519.SH"][0]["report_date"], "2026-06-30")
        self.assertEqual(result["_data_quality"]["600519.SH"]["row_count"], 1)

    def test_nested_data_rows_are_extracted(self) -> None:
        result = normalize_a_stock_financials_result(
            {"data": {"rows": [{"end_date": "2026-06-30", "eps": 1.23}]}},
            "600519.SH",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["600519.SH"][0]["eps"], 1.23)

    def test_single_financial_row_dict_is_supported(self) -> None:
        result = normalize_a_stock_financials_result(
            {"reportDate": "2026-06-30", "netProfit": 88},
            "600519.SH",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["600519.SH"][0]["report_date"], "2026-06-30")
        self.assertEqual(result["data"]["600519.SH"][0]["net_profit"], 88)

    def test_malformed_scalar_is_missing_without_exception(self) -> None:
        result = normalize_a_stock_financials_result("bad payload", "600519.SH")  # type: ignore[arg-type]

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertEqual(quality["freshness_status"], "missing")
        self.assertIn("unsupported raw financials payload type: str", quality["errors"])

    def test_non_dict_rows_are_ignored_and_warned(self) -> None:
        result = normalize_a_stock_financials_result(["bad"], "600519.SH")  # type: ignore[list-item]

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertIn("no_dict_rows", quality["warnings"])

    def test_latest_date_uses_most_recent_period(self) -> None:
        result = normalize_a_stock_financials_result(
            [{"报告期": "2025-12-31"}, {"报告期": "2026-03-31"}],
            "600519.SH",
        )

        self.assertEqual(result["_data_quality"]["600519.SH"]["latest_date"], "2026-03-31")

    def test_compact_numeric_date_can_sort(self) -> None:
        result = normalize_a_stock_financials_result(
            [{"report_date": "20251231"}, {"report_date": "20260331"}],
            "600519.SH",
        )

        self.assertEqual(result["_data_quality"]["600519.SH"]["latest_date"], "20260331")

    def test_warnings_are_preserved_from_payload(self) -> None:
        result = normalize_a_stock_financials_result(
            {"warnings": ["rate limited"], "data": [{"报告期": "2026-03-31"}]},
            "600519.SH",
        )

        self.assertIn("rate limited", result["_data_quality"]["600519.SH"]["warnings"])

    def test_message_on_success_is_warning(self) -> None:
        result = normalize_a_stock_financials_result(
            {"ok": True, "message": "partial data", "data": [{"报告期": "2026-03-31"}]},
            "600519.SH",
        )

        self.assertIn("partial data", result["_data_quality"]["600519.SH"]["warnings"])

    def test_source_defaults_to_a_stock_data(self) -> None:
        result = normalize_a_stock_financials_result([{"报告期": "2026-03-31"}], "600519.SH")

        self.assertEqual(result["source"], "a_stock_data")
        self.assertEqual(result["_data_quality"]["600519.SH"]["source"], "a_stock_data")
        self.assertEqual(result["upstream"], "unknown")

    def test_raw_row_is_preserved_for_audit(self) -> None:
        raw = {"报告期": "2026-03-31", "custom_field": "kept"}
        result = normalize_a_stock_financials_result([raw], "600519.SH")

        self.assertEqual(result["data"]["600519.SH"][0]["raw"], raw)

    def test_quality_contains_source_summary_contract_keys(self) -> None:
        result = normalize_a_stock_financials_result([{"报告期": "2026-03-31"}], "600519.SH")
        quality = result["_data_quality"]["600519.SH"]

        for key in (
            "tool_name",
            "freshness_status",
            "source",
            "source_error",
            "warnings",
            "row_count",
            "facts_available",
            "facts_unavailable",
        ):
            self.assertIn(key, quality)

    def test_error_list_is_preserved(self) -> None:
        result = normalize_a_stock_financials_result(
            {"ok": False, "errors": ["E1", "E2"]},
            "600519.SH",
        )

        self.assertEqual(result["_data_quality"]["600519.SH"]["errors"], ["E1", "E2"])

    def test_empty_dict_is_missing(self) -> None:
        result = normalize_a_stock_financials_result({}, "600519.SH")

        self.assertFalse(result["ok"])
        self.assertEqual(result["_data_quality"]["600519.SH"]["freshness_status"], "missing")


if __name__ == "__main__":
    unittest.main()
