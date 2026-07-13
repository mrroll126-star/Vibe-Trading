from __future__ import annotations

import json
import unittest

from src.reports import generate_research_artifact, serialize_tool_result


SYMBOL = "600519.SH"


def market_result() -> dict:
    return {
        "ok": True,
        "data": {SYMBOL: [{"date": "2026-07-10", "close": 1500.5}]},
        "_data_quality": {
            SYMBOL: {
                "provider": "fixture_market",
                "source": "fixture_market_data",
                "upstream": "fixture",
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


def as_trace_event(serialized: dict) -> dict:
    return {
        "type": "tool_result",
        "tool": serialized["tool_name"],
        "status": serialized["status"],
        "result": serialized["structured_payload"],
    }


class ToolResultSerializerTests(unittest.TestCase):
    def test_financial_structured_output_preserves_provenance(self) -> None:
        serialized = serialize_tool_result(
            tool_name="get_financial_statements",
            raw_result=financial_result("income"),
        )

        self.assertEqual(serialized["structured_payload"]["statement_type"], "income")
        self.assertEqual(serialized["metadata"]["provider"], "a_stock_data")
        self.assertEqual(serialized["metadata"]["source"], "sina_financial_report")
        self.assertEqual(serialized["metadata"]["upstream"], "sina")
        self.assertEqual(serialized["warnings"], [])

    def test_market_structured_json_output_preserves_quality(self) -> None:
        serialized = serialize_tool_result(
            tool_name="get_market_data",
            raw_result=json.dumps(market_result()),
        )

        self.assertEqual(serialized["status"], "ok")
        self.assertEqual(serialized["metadata"]["provider"], "fixture_market")
        self.assertIn(SYMBOL, serialized["metadata"]["data_quality"])

    def test_legacy_text_is_not_interpreted_as_facts(self) -> None:
        serialized = serialize_tool_result(
            tool_name="get_financial_statements",
            raw_result="Income was 100, profit was 20.",
        )

        self.assertIsNone(serialized["structured_payload"])
        self.assertIn("legacy_unstructured_result", serialized["warnings"])
        self.assertNotIn("100", serialized["human_summary"])

    def test_missing_metadata_warns_without_changing_payload(self) -> None:
        serialized = serialize_tool_result(
            tool_name="get_market_data",
            raw_result={"ok": True, "data": {SYMBOL: [{"close": 1}]}},
        )

        self.assertEqual(serialized["structured_payload"]["data"][SYMBOL][0]["close"], 1)
        self.assertIn("metadata_provider_missing", serialized["warnings"])
        self.assertIn("metadata_source_missing", serialized["warnings"])
        self.assertIn("metadata_data_quality_missing", serialized["warnings"])

    def test_structured_payload_is_artifact_compatible(self) -> None:
        events = [as_trace_event(serialize_tool_result(tool_name="get_market_data", raw_result=market_result()))]
        for statement in ("income", "balance", "cashflow"):
            events.append(
                as_trace_event(
                    serialize_tool_result(
                        tool_name="get_financial_statements",
                        raw_result=financial_result(statement),
                    )
                )
            )
        events.append({"type": "answer", "content": "Fixture-only interpretation."})

        artifact = generate_research_artifact(
            run_id="serializer-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")
        self.assertEqual(
            artifact["research_report"]["data_confidence"]["financial_data"]["provider"],
            "a_stock_data",
        )


if __name__ == "__main__":
    unittest.main()
