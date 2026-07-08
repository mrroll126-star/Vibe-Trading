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
from src.agent.tools import ToolRegistry
from src.agent.trace import TraceWriter


class SymbolIntentGuardIntegrationTests(unittest.TestCase):
    def _make_agent(self) -> tuple[AgentLoop, ContextBuilder, list, TraceWriter, list]:
        registry = ToolRegistry()
        agent = AgentLoop(registry=registry, llm=object())
        agent._current_user_message = ""
        context = ContextBuilder(registry, agent.memory)
        messages: list = []
        react_trace: list = []
        trace_dir = tempfile.TemporaryDirectory()
        self.addCleanup(trace_dir.cleanup)
        trace = TraceWriter(Path(trace_dir.name))
        return agent, context, messages, trace, react_trace

    @staticmethod
    def _tc(name: str, arguments: dict) -> SimpleNamespace:
        return SimpleNamespace(id=f"tc_{name}", name=name, arguments=arguments)

    @staticmethod
    def _last_payload(messages: list) -> dict:
        return json.loads(messages[-1]["content"])

    def _run_single(self, prompt: str, tool_name: str, args: dict, *, flag: bool) -> tuple[dict, int]:
        agent, context, messages, trace, react_trace = self._make_agent()
        agent._current_user_message = prompt
        calls = {"count": 0}

        def fake_invoke(name, invoke_args):
            calls["count"] += 1
            return json.dumps({"ok": True, "tool": name, "args": invoke_args}), 7

        agent._invoke_tool = fake_invoke  # type: ignore[method-assign]
        env_value = "1" if flag else ""
        with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD": env_value}, clear=False):
            agent._execute_single(self._tc(tool_name, args), context, messages, trace, react_trace, 1)
        trace.close()
        return self._last_payload(messages), calls["count"]

    def test_flag_off_does_not_intercept_ambiguous_symbol(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001",
            "get_market_data",
            {"codes": ["000001.SZ"]},
            flag=False,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertNotIn("_symbol_intent_guard", payload)

    def test_flag_on_allows_safe_a_share_symbol(self) -> None:
        payload, calls = self._run_single(
            "请分析 600519",
            "get_market_data",
            {"codes": ["600519.SH"]},
            flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_allows_safe_us_symbol(self) -> None:
        payload, calls = self._run_single(
            "Analyze QQQ",
            "get_market_data",
            {"codes": ["QQQ.US"]},
            flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_allows_safe_hk_symbol(self) -> None:
        payload, calls = self._run_single(
            "请分析 00700",
            "get_market_data",
            {"codes": ["00700.HK"]},
            flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_clarifies_ambiguous_000001(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001",
            "get_market_data",
            {"codes": ["000001.SZ"]},
            flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertEqual(payload["decision"], "clarify")
        self.assertEqual(payload["message"], "Symbol Clarification Required")
        self.assertIn("_symbol_intent_guard", payload)

    def test_flag_on_clarifies_chinese_name(self) -> None:
        payload, calls = self._run_single(
            "请分析 贵州茅台",
            "get_market_data",
            {"codes": ["600519.SH"]},
            flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "clarify")
        self.assertIn("_symbol_intent_guard", payload)

    def test_flag_on_blocks_explicit_mismatch(self) -> None:
        payload, calls = self._run_single(
            "请分析 600519.SH",
            "get_market_data",
            {"codes": ["300750.SZ"]},
            flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["message"], "Symbol Intent Blocked")

    def test_flag_on_blocks_untraceable_symbol(self) -> None:
        payload, calls = self._run_single(
            "请分析今天市场",
            "get_market_data",
            {"codes": ["600519.SH"]},
            flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["reason"], "tool_symbol_not_traceable_to_user_prompt")

    def test_flag_on_does_not_intercept_non_market_data_tool(self) -> None:
        payload, calls = self._run_single(
            "请分析 600519",
            "get_stock_news",
            {"code": "600519.SH"},
            flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_blocked_result_has_no_market_data_quality(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001",
            "get_market_data",
            {"codes": ["000001.SZ"]},
            flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertNotIn("_data_quality", payload)
        self.assertNotIn("000001.SZ", payload)
        self.assertEqual(payload["error_code"], "pre_tool_symbol_intent_guard")


if __name__ == "__main__":
    unittest.main()
