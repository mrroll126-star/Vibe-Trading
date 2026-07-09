from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from src.adapters.a_stock_data.financials import (
    fetch_a_stock_financials,
    is_a_stock_financials_fallback_eligible,
    should_try_a_stock_financials_fallback,
)
from src.symbols.config import is_a_stock_data_adapter_enabled
from src.tools.financial_statements_tool import FinancialStatementsTool


class AStockDataFinancialsFallbackTests(unittest.TestCase):
    def test_flag_default_false(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_a_stock_data_adapter_enabled())

    def test_flag_true_values_enable(self) -> None:
        for value in ("1", "true", "True", "yes", "on"):
            with self.subTest(value=value), patch.dict(
                os.environ,
                {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": value},
                clear=True,
            ):
                self.assertTrue(is_a_stock_data_adapter_enabled())

    def test_flag_false_values_disable(self) -> None:
        for value in ("0", "false", "False", "no", "off", ""):
            with self.subTest(value=value), patch.dict(
                os.environ,
                {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": value},
                clear=True,
            ):
                self.assertFalse(is_a_stock_data_adapter_enabled())

    def test_600519_sh_eligible(self) -> None:
        self.assertTrue(is_a_stock_financials_fallback_eligible("600519.SH")["eligible"])

    def test_300750_sz_eligible(self) -> None:
        self.assertTrue(is_a_stock_financials_fallback_eligible("300750.SZ")["eligible"])

    def test_000001_sh_not_eligible_index(self) -> None:
        result = is_a_stock_financials_fallback_eligible("000001.SH")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["asset_type"], "index")

    def test_000300_sh_not_eligible_index(self) -> None:
        result = is_a_stock_financials_fallback_eligible("000300.SH")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["asset_type"], "index")

    def test_510300_sh_not_eligible_etf(self) -> None:
        result = is_a_stock_financials_fallback_eligible("510300.SH")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["asset_type"], "etf")

    def test_159915_sz_not_eligible_etf(self) -> None:
        result = is_a_stock_financials_fallback_eligible("159915.SZ")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["asset_type"], "etf")

    def test_qqq_us_not_eligible(self) -> None:
        self.assertFalse(is_a_stock_financials_fallback_eligible("QQQ.US")["eligible"])

    def test_00700_hk_not_eligible(self) -> None:
        self.assertFalse(is_a_stock_financials_fallback_eligible("00700.HK")["eligible"])

    def test_chinese_name_not_eligible(self) -> None:
        self.assertFalse(is_a_stock_financials_fallback_eligible("贵州茅台")["eligible"])

    def test_000001_not_eligible_ambiguous(self) -> None:
        result = is_a_stock_financials_fallback_eligible("000001")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["reason"], "symbol_requires_confirmation_or_is_invalid")

    def test_primary_none_should_try(self) -> None:
        self.assertTrue(should_try_a_stock_financials_fallback(None))

    def test_ok_false_should_try(self) -> None:
        self.assertTrue(should_try_a_stock_financials_fallback({"ok": False}))

    def test_error_should_try(self) -> None:
        self.assertTrue(should_try_a_stock_financials_fallback({"ok": True, "error": "boom"}))

    def test_empty_rows_should_try(self) -> None:
        self.assertTrue(
            should_try_a_stock_financials_fallback(
                {"ok": True, "data": {"600519.SH": {"periods": []}}}
            )
        )

    def test_data_quality_missing_should_try(self) -> None:
        self.assertTrue(
            should_try_a_stock_financials_fallback(
                {"ok": True, "_data_quality": {"600519.SH": {"freshness_status": "missing"}}}
            )
        )

    def test_ok_true_with_rows_should_not_try(self) -> None:
        self.assertFalse(
            should_try_a_stock_financials_fallback(
                {"ok": True, "data": {"600519.SH": {"periods": [{"REPORT_DATE": "2025-12-31"}]}}}
            )
        )

    def test_warning_with_data_should_not_try(self) -> None:
        self.assertFalse(
            should_try_a_stock_financials_fallback(
                {
                    "ok": True,
                    "warnings": ["partial"],
                    "data": {"600519.SH": {"periods": [{"REPORT_DATE": "2025-12-31"}]}},
                }
            )
        )

    def test_flag_off_primary_failure_does_not_call_fallback(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "0"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        fallback.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["source"], "eastmoney")
        self.assertEqual(result["error"], "primary failed")

    def test_flag_on_primary_success_does_not_call_fallback(self) -> None:
        primary = {"periods": [{"REPORT_DATE": "2025-12-31"}]}
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value=primary):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        fallback.assert_not_called()
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "eastmoney")

    def test_flag_on_primary_failure_eligible_calls_fallback(self) -> None:
        fallback_payload = {"ok": True, "data": [{"报告期": "2026-03-31", "营业收入": 100}]}
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", return_value=fallback_payload) as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH", statement="income"))

        fallback.assert_called_once()
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "a_stock_data")

    def test_fallback_raw_rows_normalize_to_a_stock_provider(self) -> None:
        fallback_payload = {"ok": True, "data": [{"报告期": "2026-03-31", "净利润": 20}], "source": "mock_source", "upstream": "mock"}
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", return_value=fallback_payload):
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        self.assertEqual(result["provider"], "a_stock_data")
        self.assertEqual(result["source"], "mock_source")

    def test_fallback_result_includes_data_quality(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", return_value=[{"报告期": "2026-03-31"}]):
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        self.assertIn("_data_quality", result)
        self.assertIn("600519.SH", result["_data_quality"])

    def test_fallback_preserves_primary_error_metadata(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", return_value=[{"报告期": "2026-03-31"}]):
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        quality = result["_data_quality"]["600519.SH"]
        self.assertEqual(quality["primary_error"], "primary failed")
        self.assertIn("primary_financials_unavailable", quality["warnings"])
        self.assertIn("a_stock_data_fallback_used", quality["warnings"])

    def test_primary_failure_index_symbol_does_not_call_fallback(self) -> None:
        result, fallback = self._execute_with_primary_failure("000001.SH")
        fallback.assert_not_called()
        self.assertIn("a_stock_data_fallback_not_eligible", result["warnings"])

    def test_primary_failure_etf_symbol_does_not_call_fallback(self) -> None:
        result, fallback = self._execute_with_primary_failure("510300.SH")
        fallback.assert_not_called()
        self.assertIn("a_stock_data_fallback_not_eligible", result["warnings"])

    def test_primary_failure_us_symbol_does_not_call_fallback(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_sec_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code="QQQ.US"))

        fallback.assert_not_called()
        self.assertIn("a_stock_data_fallback_not_eligible", result["warnings"])

    def test_fallback_error_returns_missing_quality(self) -> None:
        fallback_payload = {"ok": False, "error": "fallback failed", "data": []}
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", return_value=fallback_payload):
                    result = json.loads(FinancialStatementsTool().execute(code="600519.SH"))

        quality = result["_data_quality"]["600519.SH"]
        self.assertFalse(result["ok"])
        self.assertEqual(quality["freshness_status"], "missing")
        self.assertIn("fallback failed", quality["source_error"])
        self.assertIn("a_stock_data_fallback_failed", quality["warnings"])

    def test_default_fetch_stub_normalizes_to_missing_without_exception(self) -> None:
        raw = fetch_a_stock_financials("600519.SH", statement_type="income")
        self.assertFalse(raw["ok"])
        self.assertEqual(raw["error"], "a_stock_data_live_fetch_not_implemented")

    def _execute_with_primary_failure(self, code: str):
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code=code))
        return result, fallback


if __name__ == "__main__":
    unittest.main()
