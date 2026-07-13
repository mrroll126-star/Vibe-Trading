from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.agent.context import ContextBuilder
from src.agent.loop import AgentLoop
from src.agent.memory import WorkspaceMemory
from src.agent.tools import ToolRegistry
from src.agent.trace import TraceWriter
from src.reports.trace_collector import build_research_report_from_trace_events


SYMBOL = "600519.SH"


def financial_result(statement_type: str) -> str:
    return json.dumps(
        {
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
        },
        ensure_ascii=False,
    )


class FinancialRuntimeDualWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.env_patch.start()
        os.environ.pop("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", None)

    def tearDown(self) -> None:
        self.env_patch.stop()

    def _finalize(self, trace: TraceWriter, tool_name: str, result: str, iteration: int = 1) -> list[dict]:
        registry = ToolRegistry()
        loop = AgentLoop(registry, llm=None, memory=WorkspaceMemory())
        context = ContextBuilder(registry, loop.memory)
        messages: list[dict] = []
        loop._finalize_tool_result(
            SimpleNamespace(name=tool_name, id=f"call-{iteration}"),
            result,
            5,
            context,
            messages,
            trace,
            [],
            iteration,
        )
        return messages

    def _events_after_finalize(self, *, tool_name: str, result: str) -> tuple[list[dict], list[dict]]:
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceWriter(Path(directory))
            messages = self._finalize(trace, tool_name, result)
            trace.close()
            events = TraceWriter.read(Path(directory), resolve_offloads=True, resolve_fields={"result", "structured_payload"})
        return events, messages

    def test_flag_off_keeps_legacy_trace_shape(self) -> None:
        events, messages = self._events_after_finalize(
            tool_name="get_financial_statements",
            result=financial_result("income"),
        )
        event = events[0]

        self.assertNotIn("structured_payload", event)
        self.assertNotIn("trace_schema_version", event)
        self.assertEqual(messages[0]["content"], financial_result("income"))

    def test_flag_on_enriches_financial_trace_only(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        events, _ = self._events_after_finalize(
            tool_name="get_financial_statements",
            result=financial_result("income"),
        )
        event = events[0]

        self.assertEqual(event["trace_schema_version"], "tool_result.v1")
        self.assertEqual(event["metadata"]["provider"], "a_stock_data")
        self.assertEqual(event["metadata"]["source"], "sina_financial_report")
        self.assertEqual(event["structured_payload"]["data"][SYMBOL][0]["report_date"], "2026-03-31")

    def test_serializer_failure_keeps_legacy_trace(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        with patch("src.agent.loop.build_financial_trace_enrichment", return_value={
            "trace_schema_version": "tool_result.v1",
            "tool_name": "get_financial_statements",
            "structured_payload": None,
            "human_summary": "Structured result unavailable.",
            "metadata": {},
            "structured_trace_warnings": ["structured_payload_unavailable"],
        }):
            events, messages = self._events_after_finalize(
                tool_name="get_financial_statements",
                result=financial_result("income"),
            )
        event = events[0]

        self.assertEqual(event["result"], financial_result("income"))
        self.assertIsNone(event["structured_payload"])
        self.assertIn("structured_payload_unavailable", event["structured_trace_warnings"])
        self.assertEqual(messages[0]["content"], financial_result("income"))

    def test_financial_events_feed_report_builder_confidence(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceWriter(Path(directory))
            for iteration, statement in enumerate(("income", "balance", "cashflow"), 1):
                self._finalize(trace, "get_financial_statements", financial_result(statement), iteration)
            trace.close()
            events = TraceWriter.read(Path(directory), resolve_offloads=True, resolve_fields={"result", "structured_payload"})

        report = build_research_report_from_trace_events(
            events,
            input_symbol=SYMBOL,
            run_id="runtime-dual-write-fixture",
        )
        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(report["data_confidence"]["financial_data"]["provider"], "a_stock_data")

    def test_non_financial_tool_is_not_enriched(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        events, _ = self._events_after_finalize(
            tool_name="get_market_data",
            result=json.dumps({"ok": True, "data": {SYMBOL: []}}),
        )

        self.assertNotIn("structured_payload", events[0])


if __name__ == "__main__":
    unittest.main()
