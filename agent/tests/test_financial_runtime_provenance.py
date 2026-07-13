from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import src.agent.trace as trace_mod
from src.agent.context import ContextBuilder
from src.agent.loop import AgentLoop
from src.agent.memory import WorkspaceMemory
from src.agent.tools import ToolRegistry
from src.agent.trace import TraceWriter
from src.reports import generate_research_artifact
from src.reports.runtime_dual_write import build_financial_trace_enrichment


SYMBOL = "300750.SZ"


def primary_result(statement_type: str, *, include_periods: bool = True) -> str:
    periods = [{"REPORT_DATE": "2026-03-31", "VALUE": 1}] if include_periods else []
    return json.dumps(
        {
            "ok": True,
            "statement": statement_type,
            "data": {SYMBOL: {"periods": periods}},
        },
        ensure_ascii=False,
    )


def fallback_result(statement_type: str) -> str:
    return json.dumps(
        {
            "ok": True,
            "statement": statement_type,
            "provider": "a_stock_data",
            "source": "sina_financial_report",
            "upstream": "sina",
            "data": {SYMBOL: {"periods": [{"REPORT_DATE": "2026-03-31", "VALUE": 1}]}},
            "fallback": {
                "primary": {
                    "source": "eastmoney",
                    "ok": False,
                    "error": "primary_financials_unavailable",
                }
            },
        },
        ensure_ascii=False,
    )


def complete_execution_metadata() -> dict:
    return {
        "provider": "eastmoney",
        "source": "eastmoney_financial_report",
        "upstream": "eastmoney",
        "fallback_used": False,
        "primary_error": None,
    }


def market_result() -> str:
    return json.dumps(
        {
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
        ensure_ascii=False,
    )


class FinancialRuntimeProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.env_patch.start()
        os.environ.pop("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", None)

    def tearDown(self) -> None:
        self.env_patch.stop()

    def _finalize(
        self,
        trace: TraceWriter,
        *,
        tool_name: str,
        result: str,
        statement_type: str = "income",
        execution_metadata: dict | None = None,
        iteration: int = 1,
    ) -> list[dict]:
        registry = ToolRegistry()
        loop = AgentLoop(registry, llm=None, memory=WorkspaceMemory())
        context = ContextBuilder(registry, loop.memory)
        messages: list[dict] = []
        tool_call = SimpleNamespace(
            name=tool_name,
            id=f"call-{iteration}",
            arguments={"code": SYMBOL, "statement": statement_type},
            execution_metadata=execution_metadata or {},
        )
        loop._finalize_tool_result(
            tool_call,
            result,
            5,
            context,
            messages,
            trace,
            [],
            iteration,
        )
        return messages

    def _single_event(
        self,
        *,
        tool_name: str = "get_financial_statements",
        result: str | None = None,
        execution_metadata: dict | None = None,
    ) -> tuple[dict, list[dict]]:
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceWriter(Path(directory))
            messages = self._finalize(
                trace,
                tool_name=tool_name,
                result=result or primary_result("income"),
                execution_metadata=execution_metadata,
            )
            trace.close()
            event = TraceWriter.read(
                Path(directory),
                resolve_offloads=True,
                resolve_fields={"result", "structured_payload"},
            )[0]
        return event, messages

    def test_flag_off_keeps_legacy_event_without_provenance(self) -> None:
        event, messages = self._single_event(execution_metadata=complete_execution_metadata())

        self.assertNotIn("structured_payload", event)
        self.assertNotIn("metadata", event)
        self.assertEqual(messages[0]["content"], primary_result("income"))

    def test_flag_on_projects_complete_explicit_primary_metadata(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        event, _ = self._single_event(execution_metadata=complete_execution_metadata())

        metadata = event["metadata"]
        self.assertEqual(metadata["provider"], "eastmoney")
        self.assertEqual(metadata["source"], "eastmoney_financial_report")
        self.assertEqual(metadata["upstream"], "eastmoney")
        self.assertEqual(metadata["statement_type"], "income")
        self.assertEqual(metadata["reporting_period"]["latest"], "2026-03-31")
        self.assertEqual(metadata["row_count"], 1)
        self.assertFalse(metadata["fallback_status"]["used"])
        self.assertEqual(metadata["data_quality"][SYMBOL]["quality_status"], "available")
        self.assertEqual(event["structured_trace_warnings"], [])

    def test_source_missing_is_not_filled_from_provider(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        metadata = complete_execution_metadata()
        metadata["source"] = ""
        event, _ = self._single_event(execution_metadata=metadata)

        self.assertEqual(event["metadata"]["source"], "")
        self.assertIn("financial_source_missing", event["structured_trace_warnings"])

    def test_provider_missing_is_not_guessed_from_tool_name(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        metadata = complete_execution_metadata()
        metadata["provider"] = ""
        event, _ = self._single_event(execution_metadata=metadata)

        self.assertEqual(event["metadata"]["provider"], "")
        self.assertIn("financial_provider_missing", event["structured_trace_warnings"])

    def test_fallback_preserves_real_provenance_and_primary_error(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        event, _ = self._single_event(
            result=fallback_result("income"),
            execution_metadata={},
        )

        metadata = event["metadata"]
        self.assertEqual(metadata["provider"], "a_stock_data")
        self.assertEqual(metadata["source"], "sina_financial_report")
        self.assertEqual(metadata["upstream"], "sina")
        self.assertTrue(metadata["fallback_status"]["used"])
        self.assertEqual(metadata["fallback_status"]["primary_error"], "primary_financials_unavailable")

    def test_malformed_payload_keeps_legacy_result_and_warns(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        event, messages = self._single_event(
            result=primary_result("income", include_periods=False),
            execution_metadata=complete_execution_metadata(),
        )

        self.assertEqual(event["result"], primary_result("income", include_periods=False))
        self.assertIn("financial_rows_missing", event["structured_trace_warnings"])
        self.assertEqual(messages[0]["content"], primary_result("income", include_periods=False))

    def test_serializer_failure_keeps_legacy_result(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        with patch("src.reports.runtime_dual_write.create_dual_write_tool_event", side_effect=RuntimeError("fixture")):
            event, messages = self._single_event(execution_metadata=complete_execution_metadata())

        self.assertEqual(event["result"], primary_result("income"))
        self.assertIsNone(event["structured_payload"])
        self.assertIn("structured_payload_unavailable", event["structured_trace_warnings"])
        self.assertEqual(messages[0]["content"], primary_result("income"))

    def test_projector_failure_preserves_structured_payload(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        with patch(
            "src.reports.runtime_dual_write.build_financial_provenance_enrichment",
            side_effect=RuntimeError("fixture"),
        ):
            event, _ = self._single_event(execution_metadata=complete_execution_metadata())

        self.assertIsInstance(event["structured_payload"], dict)
        self.assertIn("financial_provenance_projection_failed", event["structured_trace_warnings"])

    def test_non_financial_tool_is_not_enriched(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        event, _ = self._single_event(tool_name="get_market_data", result=market_result())

        self.assertNotIn("structured_payload", event)
        self.assertNotIn("metadata", event)

    def test_complete_runtime_events_generate_complete_artifact(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        with tempfile.TemporaryDirectory() as directory:
            trace_path = Path(directory)
            trace = TraceWriter(trace_path)
            trace.write_tool_result(
                call_id="market",
                result=market_result(),
                tool_name="get_market_data",
                status="ok",
                elapsed_ms=1,
                iteration=1,
            )
            for index, statement in enumerate(("income", "balance", "cashflow"), 1):
                self._finalize(
                    trace,
                    result=primary_result(statement),
                    statement_type=statement,
                    execution_metadata=complete_execution_metadata(),
                    iteration=index + 1,
                    tool_name="get_financial_statements",
                )
            trace.write_text_entry(
                {"type": "answer", "iter": 5},
                field="content",
                value="Fixture answer.",
                offload_kind="answer",
            )
            trace.close()
            events = TraceWriter.read(
                trace_path,
                resolve_offloads=True,
                resolve_fields={"result", "content", "structured_payload"},
            )

        artifact = generate_research_artifact(
            run_id="runtime-provenance-complete",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )
        self.assertEqual(artifact["research_report"]["financial_health"]["status"], "complete")
        self.assertEqual(artifact["artifact_meta"]["status"], "complete")

    def test_incomplete_provenance_generates_partial_artifact(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        metadata = complete_execution_metadata()
        metadata["provider"] = ""
        events = [
            {
                "type": "tool_result",
                "tool": "get_market_data",
                "status": "ok",
                "result": json.loads(market_result()),
            }
        ]
        for statement in ("income", "balance", "cashflow"):
            enrichment = build_financial_trace_enrichment(
                tool_name="get_financial_statements",
                redacted_result=primary_result(statement),
                tool_args={"code": SYMBOL, "statement": statement},
                execution_metadata=metadata,
            )
            events.append(
                {
                    "type": "tool_result",
                    "tool": "get_financial_statements",
                    "status": "ok",
                    "result": "legacy financial text",
                    "structured_payload": enrichment["structured_payload"],
                    "metadata": enrichment["metadata"],
                }
            )
        events.append({"type": "answer", "content": "Fixture answer."})

        artifact = generate_research_artifact(
            run_id="runtime-provenance-partial",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )
        self.assertEqual(artifact["artifact_meta"]["status"], "partial")
        self.assertIn("provider_missing", artifact["research_report"]["data_confidence"]["warnings"])

    def test_offloaded_structured_payload_retains_metadata_and_resolves_safely(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        old_threshold = trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD
        trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = 8
        try:
            with tempfile.TemporaryDirectory() as directory:
                trace_path = Path(directory)
                enrichment = build_financial_trace_enrichment(
                    tool_name="get_financial_statements",
                    redacted_result=primary_result("income"),
                    tool_args={"code": SYMBOL, "statement": "income"},
                    execution_metadata=complete_execution_metadata(),
                )
                trace = TraceWriter(trace_path)
                trace.write_tool_result(
                    call_id="income",
                    result=primary_result("income"),
                    tool_name="get_financial_statements",
                    status="ok",
                    elapsed_ms=1,
                    iteration=1,
                    enrichment=enrichment,
                )
                trace.close()
                raw_event = json.loads((trace_path / "trace.jsonl").read_text(encoding="utf-8"))
                resolved_event = TraceWriter.read(
                    trace_path,
                    resolve_offloads=True,
                    resolve_fields={"structured_payload"},
                )[0]
        finally:
            trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = old_threshold

        self.assertTrue(raw_event["structured_payload_path"].startswith("structured-tool-results/"))
        self.assertNotIn(str(trace_path), raw_event["structured_payload_path"])
        self.assertEqual(resolved_event["metadata"]["provider"], "eastmoney")
        self.assertIsInstance(json.loads(resolved_event["structured_payload"]), dict)


if __name__ == "__main__":
    unittest.main()
