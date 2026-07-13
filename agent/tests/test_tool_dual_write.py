from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.reports import generate_research_artifact
from src.reports.tool_dual_write import create_dual_write_tool_event


SYMBOL = "600519.SH"


def market_result() -> dict:
    return {
        "ok": True,
        "data": {SYMBOL: [{"date": "2026-07-10", "close": 1500.5}]},
        "_data_quality": {
            SYMBOL: {
                "provider": "fixture_market",
                "source": "fixture_market_data",
                "latest_data_date": "2026-07-10",
                "warnings": [],
            }
        },
    }


def financial_result(statement_type: str) -> dict:
    return {
        "ok": True,
        "statement_type": statement_type,
        "provider": "a_stock_data",
        "source": "sina_financial_report",
        "upstream": "sina",
        "fallback": True,
        "data": {SYMBOL: [{"report_date": "2026-03-31", "value": 1}]},
        "_data_quality": {
            SYMBOL: {
                "provider": "a_stock_data",
                "source": "sina_financial_report",
                "upstream": "sina",
                "latest_data_date": "2026-03-31",
                "warnings": ["a_stock_data_fallback_used"],
            }
        },
    }


class ToolDualWriteTests(unittest.TestCase):
    def test_financial_success_keeps_legacy_and_structured_provenance(self) -> None:
        raw = json.dumps(financial_result("income"), ensure_ascii=False)
        event = create_dual_write_tool_event(
            tool_name="get_financial_statements",
            args={"code": SYMBOL, "statement": "income"},
            raw_result=raw,
        )

        self.assertEqual(event["result"], raw)
        self.assertEqual(event["structured_payload"]["statement_type"], "income")
        self.assertEqual(event["metadata"]["provider"], "a_stock_data")
        self.assertEqual(event["metadata"]["source"], "sina_financial_report")
        self.assertEqual(event["structured_payload"]["data"][SYMBOL][0]["report_date"], "2026-03-31")

    def test_market_success_has_structured_payload(self) -> None:
        event = create_dual_write_tool_event(
            tool_name="get_market_data",
            args={"codes": [SYMBOL]},
            raw_result=market_result(),
        )

        self.assertEqual(event["structured_payload"]["data"][SYMBOL][0]["close"], 1500.5)
        self.assertEqual(event["metadata"]["provider"], "fixture_market")

    def test_serializer_failure_keeps_legacy_result(self) -> None:
        raw = json.dumps(financial_result("income"), ensure_ascii=False)
        with patch("src.reports.tool_dual_write.serialize_tool_result", side_effect=RuntimeError("fixture")):
            event = create_dual_write_tool_event(
                tool_name="get_financial_statements",
                args={"code": SYMBOL},
                raw_result=raw,
            )

        self.assertEqual(event["result"], raw)
        self.assertIsNone(event["structured_payload"])
        self.assertIn("structured_payload_unavailable", event["structured_trace_warnings"])

    def test_dual_write_events_generate_complete_artifact(self) -> None:
        events = [
            create_dual_write_tool_event(
                tool_name="get_market_data",
                args={"codes": [SYMBOL]},
                raw_result=market_result(),
            )
        ]
        for statement in ("income", "balance", "cashflow"):
            events.append(
                create_dual_write_tool_event(
                    tool_name="get_financial_statements",
                    args={"code": SYMBOL, "statement": statement},
                    raw_result=financial_result(statement),
                )
            )
        events.append({"type": "answer", "content": "Fixture interpretation."})

        artifact = generate_research_artifact(
            run_id="dual-write-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")

    def test_unknown_tool_keeps_valid_event_shape(self) -> None:
        event = create_dual_write_tool_event(
            tool_name="unknown_tool",
            args={"value": "fixture"},
            raw_result="legacy tool text",
        )

        self.assertEqual(event["type"], "tool_result")
        self.assertEqual(event["result"], "legacy tool text")
        self.assertIsNone(event["structured_payload"])
        self.assertIn("unsupported_tool_for_structured_payload", event["structured_trace_warnings"])


if __name__ == "__main__":
    unittest.main()
