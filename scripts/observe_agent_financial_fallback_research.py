#!/usr/bin/env python3
"""Observe AgentLoop consumption of a-stock-data financial fallback.

This script runs a tightly scoped AgentLoop with only the
``get_financial_statements`` tool available. It forces the primary A-share
financial provider to fail, enables the a-stock-data fallback only inside this
process, and records whether the final agent answer consumes the fallback data.

It does not start Web UI, modify provider chains, read ``agent/.env`` directly,
or require shell tools.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from src.adapters.a_stock_data.financials import fetch_a_stock_financials as live_fetch  # noqa: E402
from src.agent.loop import AgentLoop  # noqa: E402
from src.providers.chat import ChatLLM  # noqa: E402
from src.tools import build_filtered_registry  # noqa: E402


DEFAULT_PROMPT = (
    "分析贵州茅台（600519.SH）的最新财务情况，包括收入、利润、资产负债和现金流，"
    "并说明主要风险。只使用实际获取到的数据，不要估算。请说明数据来源和报告期；"
    "如果没有拿到实时或当天财务数据，请明确说明财务报表不是实时数据。"
)

FORCED_PRIMARY_FAILURE = {
    "ok": False,
    "error": "forced_primary_failure_for_agent_financial_fallback_observation",
    "data": [],
}

OBSERVATION_ENV = {
    "VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1",
    "VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD": "1",
    "VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD": "1",
    "VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY": "0",
    "VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER": "0",
    "VIBE_TRADING_ENABLE_SHELL_TOOLS": "0",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled AgentLoop observation for a-stock-data financial fallback."
    )
    parser.add_argument("--symbol", default="600519.SH", help="Explicit A-share symbol to observe.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt passed to AgentLoop.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Live fallback request timeout seconds.")
    parser.add_argument("--max-iterations", type=int, default=8, help="AgentLoop max iterations.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional ignored local directory for compact JSON summaries, e.g. local_reports.",
    )
    return parser.parse_args()


def _event_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Keep event summaries compact and non-sensitive."""
    compact: dict[str, Any] = {}
    for key, value in data.items():
        if key == "preview" and isinstance(value, str):
            compact[key] = value[:500]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            compact[key] = value
        elif isinstance(value, dict):
            compact[key] = {str(k): str(v)[:200] for k, v in value.items()}
        else:
            compact[key] = str(value)[:200]
    return compact


def _tool_calls_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") == "tool_call":
            payload = event.get("data")
            if isinstance(payload, dict):
                calls.append(
                    {
                        "tool": payload.get("tool"),
                        "arguments": payload.get("arguments"),
                        "iter": payload.get("iter"),
                    }
                )
    return calls


def _financial_call_summary(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [call for call in calls if call.get("tool") == "get_financial_statements"]


def _write_report(payload: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"a_stock_agent_financial_fallback_observation_{timestamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_observation(args: argparse.Namespace) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    live_calls: list[dict[str, Any]] = []

    def event_callback(event_type: str, data: dict[str, Any]) -> None:
        if event_type in {"tool_call", "tool_result", "stream_reset"}:
            events.append({"event_type": event_type, "data": _event_payload(data)})

    def fetch_with_timeout(symbol_arg: str, statement_type: str | None = None, **kwargs: Any) -> dict[str, Any]:
        kwargs["timeout"] = args.timeout
        live_calls.append(
            {
                "symbol": symbol_arg,
                "statement_type": statement_type,
                "timeout": args.timeout,
            }
        )
        return live_fetch(symbol_arg, statement_type=statement_type, **kwargs)

    registry = build_filtered_registry(["get_financial_statements"], include_shell_tools=False)
    llm = ChatLLM()
    agent = AgentLoop(
        registry,
        llm,
        event_callback=event_callback,
        max_iterations=args.max_iterations,
    )

    with patch.dict(os.environ, OBSERVATION_ENV, clear=False):
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=FORCED_PRIMARY_FAILURE,
        ):
            with patch(
                "src.tools.financial_statements_tool.fetch_a_stock_financials",
                side_effect=fetch_with_timeout,
            ):
                result = agent.run(args.prompt, session_id="")

    final_content = str(result.get("content") or "")
    data_quality = getattr(agent, "_data_quality", {})
    tool_calls = _tool_calls_from_events(events)
    financial_calls = _financial_call_summary(tool_calls)
    warnings: list[str] = []
    latest_dates: list[str] = []
    providers: list[str] = []
    sources: list[str] = []
    upstreams: list[str] = []
    if isinstance(data_quality, dict):
        for meta in data_quality.values():
            if not isinstance(meta, dict):
                continue
            for warning in meta.get("warnings") or []:
                if isinstance(warning, str) and warning not in warnings:
                    warnings.append(warning)
            for field, bucket in (
                ("latest_data_date", latest_dates),
                ("provider", providers),
                ("source", sources),
                ("upstream", upstreams),
            ):
                value = meta.get(field)
                if isinstance(value, str) and value and value not in bucket:
                    bucket.append(value)

    observation = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": "scripts/observe_agent_financial_fallback_research.py",
        "prompt": args.prompt,
        "symbol": args.symbol,
        "env_flags": OBSERVATION_ENV,
        "forced_primary_failure": FORCED_PRIMARY_FAILURE,
        "agent_result": {
            "status": result.get("status"),
            "run_id": result.get("run_id"),
            "run_dir": result.get("run_dir"),
            "iterations": result.get("iterations"),
            "max_iterations": result.get("max_iterations"),
            "error_code": result.get("error_code"),
            "reason": result.get("reason"),
        },
        "tool_calls": tool_calls,
        "financial_tool_calls": financial_calls,
        "live_fallback_calls": live_calls,
        "data_quality_keys": sorted(data_quality.keys()) if isinstance(data_quality, dict) else [],
        "data_quality": data_quality if isinstance(data_quality, dict) else {},
        "answer_checks": {
            "has_final_answer": bool(final_content.strip()),
            "mentions_a_stock_data": "a_stock_data" in final_content or "a-stock-data" in final_content,
            "mentions_sina": "sina" in final_content.lower() or "新浪" in final_content,
            "mentions_report_date": any(date in final_content for date in latest_dates),
            "has_data_source_summary": "Data Source Summary" in final_content,
            "has_source_warnings": "Source Warnings" in final_content,
            "mentions_no_realtime_limit": any(
                phrase in final_content
                for phrase in ("不是实时", "非实时", "报告期", "截至", "not real-time", "not realtime")
            ),
            "has_no_estimate_warning": "No Estimate Warning" in final_content,
        },
        "fallback_checks": {
            "financial_tool_called": bool(financial_calls),
            "live_fallback_called": bool(live_calls),
            "provider_values": providers,
            "source_values": sources,
            "upstream_values": upstreams,
            "latest_data_dates": latest_dates,
            "warnings": warnings,
            "primary_unavailable_warning": "primary_financials_unavailable" in warnings,
            "fallback_used_warning": "a_stock_data_fallback_used" in warnings,
            "no_symbol_clarification_block": "Symbol Clarification Required" not in final_content,
            "no_benchmark_policy": "_benchmark_policy" not in final_content,
            "no_asset_routing_block": "tool_routing_blocked" not in final_content,
        },
        "final_answer_excerpt": final_content[:2500],
    }
    return observation


def main() -> int:
    args = parse_args()
    observation = run_observation(args)

    agent_result = observation["agent_result"]
    checks = observation["fallback_checks"]
    answer_checks = observation["answer_checks"]
    print(f"status={agent_result.get('status')} run_id={agent_result.get('run_id')}")
    print(f"iterations={agent_result.get('iterations')}/{agent_result.get('max_iterations')}")
    print(f"financial_tool_calls={len(observation['financial_tool_calls'])}")
    print(f"live_fallback_calls={len(observation['live_fallback_calls'])}")
    print(f"providers={checks['provider_values']}")
    print(f"sources={checks['source_values']}")
    print(f"latest_data_dates={checks['latest_data_dates']}")
    print(f"warnings={checks['warnings']}")
    print(f"answer_checks={answer_checks}")
    print(f"guard_checks={{{', '.join(f'{k}: {v}' for k, v in checks.items() if k.startswith('no_'))}}}")

    if observation["financial_tool_calls"]:
        print("financial_tool_call_args=")
        for call in observation["financial_tool_calls"]:
            print(json.dumps(call, ensure_ascii=False))

    if args.output_dir:
        report_path = _write_report(observation, (ROOT / args.output_dir).resolve())
        print(f"JSON report: {report_path}")

    required = [
        agent_result.get("status") == "success",
        checks["financial_tool_called"],
        checks["live_fallback_called"],
        "a_stock_data" in checks["provider_values"],
        "sina_financial_report" in checks["source_values"],
        checks["primary_unavailable_warning"],
        checks["fallback_used_warning"],
        answer_checks["has_final_answer"],
        answer_checks["has_data_source_summary"],
    ]
    return 0 if all(required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
