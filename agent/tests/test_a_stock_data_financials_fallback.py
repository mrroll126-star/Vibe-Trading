from __future__ import annotations

import json
import os
import unittest
from unittest.mock import Mock, patch

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

    def test_fetch_income_parses_sina_rows(self) -> None:
        response = _mock_response(
            {
                "result": {
                    "data": {
                        "report_list": {
                            "20260331": {
                                "data": [
                                    {"item_title": "营业收入", "item_value": "100", "item_tongbi": "5%"},
                                    {"item_title": "净利润", "item_value": "20", "item_tongbi": ""},
                                ]
                            }
                        }
                    }
                }
            }
        )
        with patch("src.adapters.a_stock_data.financials.requests.get", return_value=response) as get:
            raw = fetch_a_stock_financials("600519.SH", statement_type="income", num=3, timeout=7)

        self.assertTrue(raw["ok"])
        self.assertEqual(raw["source"], "sina_financial_report")
        self.assertEqual(raw["upstream"], "a-stock-data")
        self.assertEqual(raw["data"][0]["报告期"], "2026-03-31")
        self.assertEqual(raw["data"][0]["营业收入"], "100")
        self.assertEqual(raw["data"][0]["营业收入_同比"], "5%")
        self.assertEqual(raw["data"][0]["净利润"], "20")
        args, kwargs = get.call_args
        self.assertIn("CompanyFinanceService.getFinanceReport2022", args[0])
        self.assertEqual(kwargs["params"]["paperCode"], "sh600519")
        self.assertEqual(kwargs["params"]["source"], "lrb")
        self.assertEqual(kwargs["timeout"], 7)

    def test_fetch_balance_uses_fzb(self) -> None:
        with patch("src.adapters.a_stock_data.financials.requests.get", return_value=_mock_response(_payload_with_period())) as get:
            raw = fetch_a_stock_financials("300750.SZ", statement_type="balance")

        self.assertTrue(raw["ok"])
        self.assertEqual(get.call_args.kwargs["params"]["paperCode"], "sz300750")
        self.assertEqual(get.call_args.kwargs["params"]["source"], "fzb")

    def test_fetch_cashflow_uses_llb(self) -> None:
        with patch("src.adapters.a_stock_data.financials.requests.get", return_value=_mock_response(_payload_with_period())) as get:
            raw = fetch_a_stock_financials("300750.SZ", statement_type="cashflow")

        self.assertTrue(raw["ok"])
        self.assertEqual(get.call_args.kwargs["params"]["source"], "llb")

    def test_fetch_unsupported_indicators_returns_missing_payload(self) -> None:
        with patch("src.adapters.a_stock_data.financials.requests.get") as get:
            raw = fetch_a_stock_financials("600519.SH", statement_type="indicators")

        get.assert_not_called()
        self.assertFalse(raw["ok"])
        self.assertIn("unsupported_statement_type", raw["error"])

    def test_fetch_request_error_returns_missing_payload(self) -> None:
        with patch("src.adapters.a_stock_data.financials.requests.get", side_effect=RuntimeError("network down")):
            raw = fetch_a_stock_financials("600519.SH", statement_type="income")

        self.assertFalse(raw["ok"])
        self.assertIn("sina_financial_report_request_failed", raw["error"])

    def test_fetch_empty_rows_returns_no_rows_error(self) -> None:
        with patch("src.adapters.a_stock_data.financials.requests.get", return_value=_mock_response({"result": {"data": {"report_list": {}}}})):
            raw = fetch_a_stock_financials("600519.SH", statement_type="income")

        self.assertFalse(raw["ok"])
        self.assertEqual(raw["error"], "sina_financial_report_returned_no_rows")

    def _execute_with_primary_failure(self, code: str):
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=True):
            with patch("src.tools.financial_statements_tool._fetch_eastmoney_statement", return_value={"error": "primary failed"}):
                with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                    result = json.loads(FinancialStatementsTool().execute(code=code))
        return result, fallback

def _payload_with_period() -> dict:
    return {
        "result": {
            "data": {
                "report_list": {
                    "20260331": {
                        "data": [
                            {"item_title": "项目", "item_value": "1", "item_tongbi": None},
                        ]
                    }
                }
            }
        }
    }


def _mock_response(payload: dict) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


if __name__ == "__main__":
    unittest.main()
