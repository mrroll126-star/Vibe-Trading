"""Fixture-only A-share financial execution-metadata producer tests."""

from __future__ import annotations

import json
import os
import unittest
from typing import Any
from unittest.mock import patch

from src.agent.tool_execution import ToolExecutionResult
from src.agent.tools import ToolRegistry
from src.reports import generate_research_artifact
from src.reports.runtime_dual_write import build_financial_trace_enrichment
from src.tools.financial_statements_tool import FinancialStatementsTool


SYMBOL = "300750.SZ"


def eastmoney_periods(statement: str) -> dict[str, Any]:
    return {
        "periods": [
            {"REPORT_DATE": "2026-03-31", "STATEMENT": statement, "VALUE": 1},
            {"REPORT_DATE": "2025-12-31", "STATEMENT": statement, "VALUE": 2},
        ]
    }


def fallback_rows() -> dict[str, Any]:
    return {
        "ok": True,
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "data": [{"报告期": "2026-03-31", "营业收入": 100}],
    }


class FinancialExecutionMetadataProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.env_patch.start()
        os.environ.pop("VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER", None)
        os.environ.pop("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", None)

    def tearDown(self) -> None:
        self.env_patch.stop()

    def _primary(self, statement: str = "income") -> ToolExecutionResult:
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=eastmoney_periods(statement),
        ):
            return FinancialStatementsTool().execute_with_metadata(
                code=SYMBOL, statement=statement, period="quarter"
            )

    def _fallback(self, *, raw_fallback: dict[str, Any] | None = None, error: str = "primary unavailable") -> ToolExecutionResult:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
            with patch(
                "src.tools.financial_statements_tool._fetch_eastmoney_statement",
                return_value={"error": error},
            ), patch(
                "src.tools.financial_statements_tool.fetch_a_stock_financials",
                return_value=raw_fallback if raw_fallback is not None else fallback_rows(),
            ):
                return FinancialStatementsTool().execute_with_metadata(
                    code=SYMBOL, statement="income", period="quarter"
                )

    def test_a_share_primary_success_produces_explicit_metadata(self) -> None:
        result = self._primary()
        payload = json.loads(result.legacy_result)
        metadata = result.execution_metadata

        self.assertIsInstance(result, ToolExecutionResult)
        self.assertTrue(payload["ok"])
        self.assertEqual(metadata["provider"], "eastmoney")
        self.assertEqual(metadata["source"], "eastmoney")
        self.assertIsNone(metadata["upstream"])
        self.assertEqual(metadata["symbol"], SYMBOL)
        self.assertEqual(metadata["statement_type"], "income")
        self.assertFalse(metadata["fallback"]["used"])
        self.assertIsNone(metadata["fallback"]["primary_error"])
        self.assertTrue(metadata["data_quality"]["provider_success"])

    def test_fallback_success_uses_final_a_stock_data_provenance(self) -> None:
        result = self._fallback()
        payload = json.loads(result.legacy_result)
        metadata = result.execution_metadata

        self.assertTrue(payload["ok"])
        self.assertEqual(metadata["provider"], "a_stock_data")
        self.assertEqual(metadata["source"], "sina_financial_report")
        self.assertEqual(metadata["upstream"], "a-stock-data")
        self.assertTrue(metadata["fallback"]["used"])
        self.assertEqual(metadata["fallback"]["primary_provider"], "eastmoney")
        self.assertEqual(metadata["fallback"]["primary_error"], "primary unavailable")
        self.assertNotEqual(metadata["provider"], "eastmoney")

    def test_primary_and_fallback_failure_never_claims_a_successful_provider(self) -> None:
        result = self._fallback(raw_fallback={"ok": False, "error": "fallback unavailable", "data": []})
        payload = json.loads(result.legacy_result)
        metadata = result.execution_metadata

        self.assertFalse(payload["ok"])
        self.assertIsNone(metadata["provider"])
        self.assertTrue(metadata["fallback"]["used"])
        self.assertFalse(metadata["data_quality"]["provider_success"])
        self.assertIn("a_stock_data_fallback_failed", metadata["warnings"])

    def test_fallback_ineligible_does_not_call_provider_and_preserves_primary_failure(self) -> None:
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
            with patch(
                "src.tools.financial_statements_tool._fetch_eastmoney_statement",
                return_value={"error": "primary unavailable"},
            ), patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                result = FinancialStatementsTool().execute_with_metadata(
                    code="510300.SH", statement="income"
                )

        metadata = result.execution_metadata
        fallback.assert_not_called()
        self.assertIsNone(metadata["provider"])
        self.assertFalse(metadata["fallback"]["used"])
        self.assertEqual(metadata["fallback"]["primary_error"], "primary unavailable")
        self.assertIn("a_stock_data_fallback_not_eligible", metadata["warnings"])

    def test_us_path_keeps_legacy_behavior_without_a_share_metadata(self) -> None:
        with patch(
            "src.tools.financial_statements_tool._fetch_sec_statement",
            return_value={"periods": [{"REPORT_DATE": "2026-03-31", "VALUE": 1}]},
        ):
            result = FinancialStatementsTool().execute_with_metadata(code="AAPL.US", statement="income")

        self.assertIsNone(result.execution_metadata)
        self.assertEqual(json.loads(result.legacy_result)["source"], "sec_edgar")

    def test_registry_legacy_and_metadata_interfaces_are_compatible(self) -> None:
        registry = ToolRegistry()
        registry.register(FinancialStatementsTool())
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=eastmoney_periods("income"),
        ):
            legacy = registry.execute("get_financial_statements", {"code": SYMBOL, "statement": "income"})
            result = registry.execute_with_metadata(
                "get_financial_statements", {"code": SYMBOL, "statement": "income"}
            )

        self.assertIsInstance(legacy, str)
        self.assertEqual(legacy, result.legacy_result)
        self.assertEqual(result.execution_metadata["provider"], "eastmoney")

    def test_primary_error_redaction_removes_common_secret_forms(self) -> None:
        error = (
            "Authorization: Bearer super-secret-token "
            "https://example.test/path?api_key=query-secret&safe=value "
            "MY_API_KEY=environment-secret "
            + "x" * 400
        )
        result = self._fallback(error=error)
        primary_error = result.execution_metadata["fallback"]["primary_error"]

        self.assertNotIn("super-secret-token", primary_error)
        self.assertNotIn("query-secret", primary_error)
        self.assertNotIn("environment-secret", primary_error)
        self.assertLessEqual(len(primary_error), 303)

    def test_runtime_enrichment_consumes_producer_metadata_without_touching_legacy_text(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        registry = ToolRegistry()
        registry.register(FinancialStatementsTool())
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=eastmoney_periods("income"),
        ):
            result = registry.execute_with_metadata(
                "get_financial_statements", {"code": SYMBOL, "statement": "income"}
            )
        enrichment = build_financial_trace_enrichment(
            tool_name="get_financial_statements",
            redacted_result=result.legacy_result,
            tool_args={"code": SYMBOL, "statement": "income"},
            execution_metadata=dict(result.execution_metadata),
        )

        self.assertEqual(enrichment["metadata"]["provider"], "eastmoney")
        self.assertEqual(enrichment["metadata"]["source"], "eastmoney")
        self.assertFalse(enrichment["metadata"]["fallback_status"]["used"])
        self.assertEqual(enrichment["human_summary"], "Structured result available for get_financial_statements.")
        self.assertNotIn("fixture_primary", enrichment["human_summary"])

    def test_three_primary_results_can_build_a_complete_offline_artifact(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        events: list[dict[str, Any]] = [
            {
                "type": "tool_result",
                "tool": "get_market_data",
                "status": "ok",
                "result": {
                    "ok": True,
                    "data": {SYMBOL: [{"date": "2026-07-10", "close": 200.0}]},
                    "_data_quality": {
                        SYMBOL: {
                            "provider": "fixture_market",
                            "source": "fixture_market_data",
                            "latest_data_date": "2026-07-10",
                            "warnings": [],
                        }
                    },
                },
            }
        ]
        for statement in ("income", "balance", "cashflow"):
            result = self._primary(statement)
            enrichment = build_financial_trace_enrichment(
                tool_name="get_financial_statements",
                redacted_result=result.legacy_result,
                tool_args={"code": SYMBOL, "statement": statement},
                execution_metadata=dict(result.execution_metadata),
            )
            events.append(
                {
                    "type": "tool_result",
                    "tool": "get_financial_statements",
                    "status": "ok",
                    "result": result.legacy_result,
                    "structured_payload": enrichment["structured_payload"],
                    "metadata": enrichment["metadata"],
                }
            )
        events.append({"type": "answer", "content": "Fixture interpretation."})

        artifact = generate_research_artifact(
            run_id="financial-metadata-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")

    def test_primary_and_fallback_metadata_do_not_cross_calls(self) -> None:
        primary = self._primary()
        fallback = self._fallback(error="primary-only-error")

        self.assertEqual(primary.execution_metadata["provider"], "eastmoney")
        self.assertIsNone(primary.execution_metadata["fallback"]["primary_error"])
        self.assertEqual(fallback.execution_metadata["provider"], "a_stock_data")
        self.assertEqual(
            fallback.execution_metadata["fallback"]["primary_error"], "primary-only-error"
        )


if __name__ == "__main__":
    unittest.main()
