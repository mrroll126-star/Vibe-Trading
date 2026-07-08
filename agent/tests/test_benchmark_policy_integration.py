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
from src.symbols.config import is_market_wide_benchmark_policy_enabled


class BenchmarkPolicyIntegrationTests(unittest.TestCase):
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

    def _run_single(self, prompt: str, tool_name: str, args: dict, *, benchmark_flag: bool) -> tuple[dict, int]:
        agent, context, messages, trace, react_trace = self._make_agent()
        agent._current_user_message = prompt
        calls = {"count": 0}

        def fake_invoke(name, invoke_args):
            calls["count"] += 1
            return json.dumps({"ok": True, "tool": name, "args": invoke_args}), 7

        agent._invoke_tool = fake_invoke  # type: ignore[method-assign]
        env = {"VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY": "1" if benchmark_flag else "0"}
        with patch.dict(os.environ, env, clear=True):
            agent._execute_single(self._tc(tool_name, args), context, messages, trace, react_trace, 1)
        trace.close()
        return self._last_payload(messages), calls["count"]

    def test_feature_flag_defaults_off(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_market_wide_benchmark_policy_enabled())
        for value in ("1", "true", "True", "yes", "on"):
            with self.subTest(value=value), patch.dict(
                os.environ,
                {"VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY": value},
                clear=True,
            ):
                self.assertTrue(is_market_wide_benchmark_policy_enabled())
        for value in ("0", "false", "False", "no", "off", ""):
            with self.subTest(value=value), patch.dict(
                os.environ,
                {"VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY": value},
                clear=True,
            ):
                self.assertFalse(is_market_wide_benchmark_policy_enabled())

    def test_flag_off_preserves_symbol_guard_block(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH"]},
            benchmark_flag=False,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertNotIn("_benchmark_policy", payload)

    def test_a_share_benchmark_allows_and_attaches_metadata(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["_benchmark_policy"]["decision"], "allow_benchmark")
        self.assertEqual(payload["_benchmark_policy"]["symbol"], "000001.SH")
        self.assertEqual(payload["_benchmark_policy"]["requested_symbols"], ["000001.SH"])
        self.assertEqual(payload["_benchmark_policy"]["allowed_symbols"], ["000001.SH"])
        self.assertEqual(payload["_benchmark_policy"]["rejected_symbols"], [])

    def test_a_share_second_benchmark_allows(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["399001.SZ"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(payload["_benchmark_policy"]["symbol"], "399001.SZ")

    def test_us_benchmark_allows(self) -> None:
        payload, calls = self._run_single(
            "美股今天怎么样",
            "get_market_data",
            {"codes": ["SPY.US"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(payload["_benchmark_policy"]["market"], "us")

    def test_hk_benchmark_allows(self) -> None:
        payload, calls = self._run_single(
            "港股今天怎么样",
            "get_market_data",
            {"codes": ["02800.HK"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(payload["_benchmark_policy"]["market"], "hk")

    def test_a_share_non_benchmark_stock_blocks(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["600519.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["_benchmark_policy"]["allowed_symbols"], [])
        self.assertEqual(payload["_benchmark_policy"]["rejected_symbols"], ["600519.SH"])

    def test_us_non_benchmark_stock_blocks(self) -> None:
        payload, calls = self._run_single(
            "美股今天怎么样",
            "get_market_data",
            {"codes": ["AAPL.US"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        self.assertEqual(payload["_benchmark_policy"]["rejected_symbols"], ["AAPL.US"])

    def test_ambiguous_market_prompt_asks_for_confirmation(self) -> None:
        payload, calls = self._run_single(
            "看看市场",
            "get_market_data",
            {"codes": ["000001.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        self.assertEqual(payload["decision"], "ask_for_confirmation")

    def test_single_target_prompt_falls_back_to_symbol_guard(self) -> None:
        payload, calls = self._run_single(
            "贵州茅台今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertNotIn("_benchmark_policy", payload)

    def test_ambiguous_000001_still_clarifies_by_symbol_guard(self) -> None:
        payload, calls = self._run_single(
            "000001 今天怎么样",
            "get_market_data",
            {"codes": ["000001.SZ"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertEqual(payload["decision"], "clarify")

    def test_company_specific_tool_blocks_before_provider(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_financial_statements",
            {"code": "000001.SH"},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        self.assertEqual(payload["decision"], "block")

    def test_global_stock_news_still_allows(self) -> None:
        payload, calls = self._run_single(
            "全市场新闻",
            "get_stock_news",
            {"scope": "global", "limit": 10},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertNotIn("_benchmark_policy", payload)

    def test_sector_ranking_still_allows(self) -> None:
        payload, calls = self._run_single(
            "板块排行",
            "get_sector_info",
            {"mode": "ranking", "limit": 20},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertTrue(payload["ok"])
        self.assertNotIn("_benchmark_policy", payload)

    def test_a_share_all_benchmark_batch_allows_and_discloses_symbols(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        policy = payload["_benchmark_policy"]
        self.assertEqual(policy["decision"], "allow_benchmark")
        self.assertEqual(policy["requested_symbols"], ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH"])
        self.assertEqual(policy["allowed_symbols"], ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH"])
        self.assertEqual(policy["rejected_symbols"], [])

    def test_a_share_mixed_benchmark_batch_blocks_and_discloses_rejected(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH", "399001.SZ", "000688.SH"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        policy = payload["_benchmark_policy"]
        self.assertEqual(policy["decision"], "block")
        self.assertEqual(policy["requested_symbols"], ["000001.SH", "399001.SZ", "000688.SH"])
        self.assertEqual(policy["allowed_symbols"], ["000001.SH", "399001.SZ"])
        self.assertEqual(policy["rejected_symbols"], ["000688.SH"])
        self.assertIn("000300.SH", policy["benchmark_universe"])

    def test_us_bare_benchmark_batch_allows(self) -> None:
        payload, calls = self._run_single(
            "美股今天怎么样",
            "get_market_data",
            {"symbols": ["SPY", "QQQ", "DIA"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(payload["_benchmark_policy"]["allowed_symbols"], ["SPY.US", "QQQ.US", "DIA.US"])

    def test_us_mixed_benchmark_batch_blocks(self) -> None:
        payload, calls = self._run_single(
            "美股今天怎么样",
            "get_market_data",
            {"symbols": ["SPY", "AAPL"]},
            benchmark_flag=True,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "market_wide_benchmark_policy")
        self.assertEqual(payload["_benchmark_policy"]["allowed_symbols"], ["SPY.US"])
        self.assertEqual(payload["_benchmark_policy"]["rejected_symbols"], ["AAPL.US"])

    def test_flag_off_preserves_existing_behavior_for_mixed_batch(self) -> None:
        payload, calls = self._run_single(
            "A股今天怎么样",
            "get_market_data",
            {"codes": ["000001.SH", "399001.SZ", "000688.SH"]},
            benchmark_flag=False,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(payload["blocked_by"], "pre_tool_symbol_intent_guard")
        self.assertNotIn("_benchmark_policy", payload)


if __name__ == "__main__":
    unittest.main()
