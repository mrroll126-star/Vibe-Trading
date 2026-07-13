"""Fixture tests for per-call legacy text and execution-metadata transport."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from src.agent.context import ContextBuilder
from src.agent.loop import AgentLoop
from src.agent.memory import WorkspaceMemory
from src.agent.tool_execution import ToolExecutionResult, normalize_tool_execution_result
from src.agent.tools import BaseTool, ToolRegistry
from src.agent.trace import TraceWriter


SYMBOL = "300750.SZ"


class _LegacyTool(BaseTool):
    name = "legacy_fixture"

    def execute(self, **kwargs: Any) -> str:
        return "legacy fixture text"


class _MetadataTool(BaseTool):
    name = "metadata_fixture"

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def execute(self, **kwargs: Any) -> ToolExecutionResult:
        return ToolExecutionResult(
            legacy_result=f"legacy {self.provider}",
            execution_metadata={"provider": self.provider, "nested": {"value": self.provider}},
        )


class _FinancialFixtureTool(BaseTool):
    name = "get_financial_statements"

    def execute(self, **kwargs: Any) -> ToolExecutionResult:
        statement = str(kwargs.get("statement") or "income")
        return ToolExecutionResult(
            legacy_result=json.dumps(
                {
                    "ok": True,
                    "statement": statement,
                    "data": {SYMBOL: {"periods": [{"REPORT_DATE": "2026-03-31", "VALUE": 1}]}},
                },
                ensure_ascii=False,
            ),
            execution_metadata={
                "provider": "fixture_primary",
                "source": "fixture_financial_source",
                "upstream": "fixture_upstream",
                "fallback": {"used": False, "primary_error": None},
            },
        )


class _ErrorTool(BaseTool):
    name = "error_fixture"

    def execute(self, **kwargs: Any) -> str:
        raise RuntimeError("fixture execution error")


class ToolExecutionResultTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.env_patch.start()
        os.environ.pop("VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE", None)

    def tearDown(self) -> None:
        self.env_patch.stop()

    def _loop(self, registry: ToolRegistry) -> AgentLoop:
        return AgentLoop(registry, llm=None, memory=WorkspaceMemory())

    def _run_single(
        self, loop: AgentLoop, *, tool_name: str, call_id: str, arguments: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        context = ContextBuilder(loop.registry, loop.memory)
        messages: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceWriter(Path(directory))
            loop._execute_single(
                SimpleNamespace(name=tool_name, id=call_id, arguments=arguments),
                context,
                messages,
                trace,
                [],
                1,
            )
            trace.close()
            events = TraceWriter.read(
                Path(directory),
                resolve_offloads=True,
                resolve_fields={"result", "structured_payload"},
            )
        return events, messages

    def test_legacy_registry_interface_and_tool_remain_string_compatible(self) -> None:
        registry = ToolRegistry()
        registry.register(_LegacyTool())

        self.assertEqual(registry.execute("legacy_fixture", {}), "legacy fixture text")
        result = registry.execute_with_metadata("legacy_fixture", {})

        self.assertEqual(result.legacy_result, "legacy fixture text")
        self.assertIsNone(result.execution_metadata)

    def test_metadata_result_is_isolated_from_source_mutation(self) -> None:
        source = {"provider": "fixture", "nested": {"items": ["before"]}}
        result = ToolExecutionResult(legacy_result="legacy", execution_metadata=source)
        source["provider"] = "changed"
        source["nested"]["items"].append("after")

        self.assertEqual(result.execution_metadata["provider"], "fixture")
        self.assertEqual(result.execution_metadata["nested"]["items"], ("before",))
        with self.assertRaises(TypeError):
            result.execution_metadata["provider"] = "mutated"  # type: ignore[index]

    def test_invalid_metadata_and_non_string_legacy_value_are_safe(self) -> None:
        result = ToolExecutionResult(legacy_result=42, execution_metadata=["invalid"])  # type: ignore[arg-type]

        self.assertEqual(result.legacy_result, "42")
        self.assertIsNone(result.execution_metadata)
        self.assertIn("execution_metadata_invalid", result.transport_warnings)
        self.assertEqual(normalize_tool_execution_result({"ok": True}).legacy_result, "{'ok': True}")

    def test_registry_error_preserves_current_json_error_semantics(self) -> None:
        registry = ToolRegistry()
        registry.register(_ErrorTool())

        result = registry.execute_with_metadata("error_fixture", {})

        self.assertIsNone(result.execution_metadata)
        payload = json.loads(result.legacy_result)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["tool"], "error_fixture")

    def test_serial_path_keeps_metadata_out_of_llm_context_and_binds_call(self) -> None:
        registry = ToolRegistry()
        registry.register(_MetadataTool("provider-a"))
        loop = self._loop(registry)
        captured: list[tuple[str, dict[str, Any] | None]] = []
        original_finalize = loop._finalize_tool_result

        def capture(*args: Any, **kwargs: Any) -> None:
            captured.append((args[0].id, kwargs.get("execution_metadata")))
            original_finalize(*args, **kwargs)

        loop._finalize_tool_result = capture  # type: ignore[method-assign]
        events, messages = self._run_single(
            loop,
            tool_name="metadata_fixture",
            call_id="call-serial",
            arguments={},
        )

        self.assertEqual(captured[0][0], "call-serial")
        self.assertEqual(captured[0][1]["provider"], "provider-a")
        self.assertEqual(messages[0]["content"], "legacy provider-a")
        self.assertEqual(events[-1]["result"], "legacy provider-a")
        self.assertNotIn("provider-a", messages[0]["content"].replace("legacy provider-a", ""))

    def test_parallel_path_isolates_per_call_metadata(self) -> None:
        registry = ToolRegistry()
        tool_a = _MetadataTool("provider-a")
        tool_a.name = "metadata_a"
        tool_b = _MetadataTool("provider-b")
        tool_b.name = "metadata_b"
        registry.register(tool_a)
        registry.register(tool_b)
        loop = self._loop(registry)
        context = ContextBuilder(registry, loop.memory)
        messages: list[dict[str, Any]] = []
        captured: dict[str, Any] = {}
        original_finalize = loop._finalize_tool_result

        def capture(*args: Any, **kwargs: Any) -> None:
            captured[args[0].id] = kwargs.get("execution_metadata")
            original_finalize(*args, **kwargs)

        loop._finalize_tool_result = capture  # type: ignore[method-assign]
        calls = [
            SimpleNamespace(name="metadata_a", id="call-a", arguments={}),
            SimpleNamespace(name="metadata_b", id="call-b", arguments={}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            trace = TraceWriter(Path(directory))
            loop._execute_parallel(calls, context, messages, trace, [], 1)
            trace.close()

        self.assertEqual(captured["call-a"]["provider"], "provider-a")
        self.assertEqual(captured["call-b"]["provider"], "provider-b")
        self.assertNotEqual(captured["call-a"], captured["call-b"])
        self.assertEqual([message["content"] for message in messages], ["legacy provider-a", "legacy provider-b"])

    def test_runtime_boundary_keeps_flag_off_trace_legacy_only(self) -> None:
        registry = ToolRegistry()
        registry.register(_FinancialFixtureTool())
        events, messages = self._run_single(
            self._loop(registry),
            tool_name="get_financial_statements",
            call_id="call-off",
            arguments={"code": SYMBOL, "statement": "income"},
        )

        result_event = events[-1]
        self.assertNotIn("structured_payload", result_event)
        self.assertNotIn("metadata", result_event)
        self.assertEqual(messages[0]["content"], result_event["result"])

    def test_runtime_boundary_projects_explicit_metadata_when_enabled(self) -> None:
        os.environ["VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE"] = "1"
        registry = ToolRegistry()
        registry.register(_FinancialFixtureTool())
        events, messages = self._run_single(
            self._loop(registry),
            tool_name="get_financial_statements",
            call_id="call-on",
            arguments={"code": SYMBOL, "statement": "income"},
        )

        result_event = events[-1]
        self.assertEqual(result_event["metadata"]["provider"], "fixture_primary")
        self.assertEqual(result_event["metadata"]["source"], "fixture_financial_source")
        self.assertEqual(result_event["metadata"]["upstream"], "fixture_upstream")
        self.assertFalse(result_event["metadata"]["fallback_status"]["used"])
        self.assertEqual(messages[0]["content"], result_event["result"])
        self.assertNotIn("fixture_financial_source", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
