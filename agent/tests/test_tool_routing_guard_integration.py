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


class ToolRoutingGuardIntegrationTests(unittest.TestCase):
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

    def _run_single(
        self,
        prompt: str,
        tool_name: str,
        args: dict,
        *,
        asset_flag: bool,
        symbol_flag: bool = False,
    ) -> tuple[dict, int]:
        agent, context, messages, trace, react_trace = self._make_agent()
        agent._current_user_message = prompt
        calls = {"count": 0}

        def fake_invoke(name, invoke_args):
            calls["count"] += 1
            return json.dumps({"ok": True, "tool": name, "args": invoke_args}), 7

        agent._invoke_tool = fake_invoke  # type: ignore[method-assign]
        env = {
            "VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD": "1" if asset_flag else "",
            "VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD": "1" if symbol_flag else "",
        }
        with patch.dict(os.environ, env, clear=False):
            agent._execute_single(self._tc(tool_name, args), context, messages, trace, react_trace, 1)
        trace.close()
        return self._last_payload(messages), calls["count"]

    def test_flag_off_does_not_intercept_index_sector_info(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_sector_info",
            {"code": "000001.SH"},
            asset_flag=False,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertNotIn("_tool_routing_guard", payload)

    def test_flag_on_allows_market_data_index(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_market_data",
            {"codes": ["000001.SH"]},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_allows_sector_info_stock(self) -> None:
        payload, calls = self._run_single(
            "请分析 600519.SH",
            "get_sector_info",
            {"code": "600519.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_allows_financial_statements_stock(self) -> None:
        payload, calls = self._run_single(
            "Analyze AAPL.US",
            "get_financial_statements",
            {"code": "AAPL.US"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_blocks_sector_info_index(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_sector_info",
            {"code": "000001.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "asset_type_tool_routing_guard")
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["asset_type"], "index")

    def test_flag_on_blocks_financial_statements_index(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_financial_statements",
            {"code": "000001.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "block")

    def test_flag_on_blocks_shareholder_count_etf(self) -> None:
        payload, calls = self._run_single(
            "请分析 510300.SH",
            "get_shareholder_count",
            {"code": "510300.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["asset_type"], "etf")

    def test_flag_on_blocks_block_trades_index(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_block_trades",
            {"code": "000001.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "block")

    def test_flag_on_unknown_asset_asks_for_confirmation(self) -> None:
        payload, calls = self._run_single(
            "请分析 UNKNOWN",
            "get_sector_info",
            {"code": "UNKNOWN"},
            asset_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["decision"], "ask_for_confirmation")
        self.assertEqual(payload["message"], "Tool Routing Requires Confirmation")

    def test_flag_on_margin_trading_etf_warns_and_calls_provider(self) -> None:
        payload, calls = self._run_single(
            "请分析 510300.SH",
            "get_margin_trading",
            {"code": "510300.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["_tool_routing_guard"]["decision"], "warn")

    def test_flag_on_stock_news_etf_warns_and_calls_provider(self) -> None:
        payload, calls = self._run_single(
            "Analyze QQQ.US",
            "get_stock_news",
            {"code": "QQQ.US"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["_tool_routing_guard"]["decision"], "warn")

    def test_flag_on_web_search_is_not_intercepted(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "web_search",
            {"query": "000001.SH"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_read_url_is_not_intercepted(self) -> None:
        payload, calls = self._run_single(
            "read this",
            "read_url",
            {"url": "https://example.com"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_flag_on_search_symbol_is_not_intercepted(self) -> None:
        payload, calls = self._run_single(
            "search symbol",
            "search_symbol",
            {"query": "000001"},
            asset_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])

    def test_symbol_intent_clarify_takes_precedence(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001",
            "get_sector_info",
            {"code": "000001.SZ"},
            asset_flag=True,
            symbol_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertNotIn("_tool_routing_guard", payload)

    def test_asset_routing_runs_after_symbol_intent_allows(self) -> None:
        payload, calls = self._run_single(
            "请分析 000001.SH",
            "get_sector_info",
            {"code": "000001.SH"},
            asset_flag=True,
            symbol_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "asset_type_tool_routing_guard")
        self.assertEqual(payload["_tool_routing_guard"]["asset_type"], "index")


if __name__ == "__main__":
    unittest.main()
