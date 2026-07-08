"""Pure market-wide benchmark routing policy.

This module does not call providers, tools, LLMs, network services, or files.
It only classifies whether a proposed tool call may use a documented benchmark
set for an explicit market-wide user request.
"""

from __future__ import annotations

import re
from typing import Any


CN_BENCHMARKS = [
    {
        "symbol": "000001.SH",
        "name": "上证指数",
        "market": "cn",
        "asset_type": "index",
        "role": "broad_market",
    },
    {
        "symbol": "399001.SZ",
        "name": "深证成指",
        "market": "cn",
        "asset_type": "index",
        "role": "broad_market",
    },
    {
        "symbol": "399006.SZ",
        "name": "创业板指",
        "market": "cn",
        "asset_type": "index",
        "role": "growth_market",
    },
    {
        "symbol": "000300.SH",
        "name": "沪深300",
        "market": "cn",
        "asset_type": "index",
        "role": "large_cap",
    },
]

US_BENCHMARKS = [
    {
        "symbol": "SPY.US",
        "name": "SPDR S&P 500 ETF",
        "market": "us",
        "asset_type": "etf",
        "role": "broad_market_proxy",
    },
    {
        "symbol": "QQQ.US",
        "name": "Invesco QQQ ETF",
        "market": "us",
        "asset_type": "etf",
        "role": "nasdaq_100_proxy",
    },
    {
        "symbol": "DIA.US",
        "name": "SPDR Dow Jones Industrial Average ETF",
        "market": "us",
        "asset_type": "etf",
        "role": "dow_proxy",
    },
    {
        "symbol": "IWM.US",
        "name": "iShares Russell 2000 ETF",
        "market": "us",
        "asset_type": "etf",
        "role": "small_cap_proxy",
    },
]

HK_BENCHMARKS = [
    {
        "symbol": "02800.HK",
        "name": "盈富基金",
        "market": "hk",
        "asset_type": "etf",
        "role": "hang_seng_proxy",
    },
    {
        "symbol": "03033.HK",
        "name": "恒生科技ETF",
        "market": "hk",
        "asset_type": "etf",
        "role": "hang_seng_tech_proxy",
    },
]

BENCHMARKS_BY_MARKET = {
    "cn": CN_BENCHMARKS,
    "us": US_BENCHMARKS,
    "hk": HK_BENCHMARKS,
}

_BENCHMARK_SYMBOLS_BY_MARKET = {
    market: {item["symbol"] for item in benchmarks}
    for market, benchmarks in BENCHMARKS_BY_MARKET.items()
}

_NO_SYMBOL_GLOBAL_NEWS_MODES = {"global", "market", "all", "sector"}
_NO_SYMBOL_SECTOR_MODES = {"ranking", "list", "overview"}
_COMPANY_SPECIFIC_TOOLS = {
    "get_financial_statements",
    "get_shareholder_count",
    "get_research_reports",
}

_KNOWN_CHINESE_TARGETS = ("贵州茅台", "腾讯", "平安银行", "苹果公司")
_KNOWN_SINGLE_TARGET_WORDS = {
    "qqq",
    "spy",
    "aapl",
    "msft",
    "nvda",
    "tsla",
    "dia",
    "iwm",
}


def evaluate_market_wide_benchmark_intent(
    original_prompt: str,
    tool_name: str | None = None,
    tool_args: dict | None = None,
) -> dict[str, Any]:
    """Evaluate whether a market-wide prompt may use benchmark symbols.

    The result is advisory only. This pure function does not alter Symbol Guard,
    Asset-type Routing Guard, provider calls, or tool arguments.
    """

    prompt = "" if original_prompt is None else str(original_prompt)
    args = tool_args if isinstance(tool_args, dict) else {}
    tool = str(tool_name or "").strip()

    no_symbol = _no_symbol_market_wide_tool(tool, args)
    if no_symbol is not None:
        return _decision(
            "not_market_wide",
            None,
            [],
            no_symbol["reason"],
            metadata={no_symbol["metadata_key"]: True, "tool_name": tool},
        )

    requested_symbols = _extract_symbols_from_args(args)
    if _is_user_specified_target(prompt):
        return _decision(
            "not_market_wide",
            None,
            [],
            "user_specified_target_intent",
            metadata={"user_specified_target": True, "tool_name": tool or None},
        )

    market = _detect_market(prompt)
    has_market_wide_intent = _has_market_wide_intent(prompt)
    if market is None:
        if _is_ambiguous_market_prompt(prompt):
            return _decision(
                "ask_for_confirmation",
                None,
                [],
                "ambiguous_market_intent_requires_market",
                warnings=["Ask the user which market they want: A-share, US, Hong Kong, or another scope."],
                metadata={"requires_market_confirmation": True, "tool_name": tool or None},
            )
        return _decision("not_market_wide", None, [], "not_market_wide")

    if not has_market_wide_intent:
        return _decision("not_market_wide", None, [], "market_mentioned_without_market_wide_intent")

    if tool and tool in _COMPANY_SPECIFIC_TOOLS:
        benchmark_universe = _benchmark_symbols_for_market(market)
        return _decision(
            "block",
            market,
            [],
            "company_specific_tool_not_eligible_for_benchmark_policy",
            warnings=["Benchmark policy does not bypass asset-type routing or company-specific tool restrictions."],
            metadata={
                "tool_name": tool,
                "requested_symbols": _canonicalize_symbols_for_market(requested_symbols, market),
                "allowed_symbols": [],
                "rejected_symbols": [],
                "benchmark_universe": benchmark_universe,
            },
        )

    canonical_symbols = _canonicalize_symbols_for_market(requested_symbols, market)
    universe_symbols = _benchmark_symbols_for_market(market)
    allowed_symbol_set = set(universe_symbols)
    allowed_symbols = [symbol for symbol in canonical_symbols if symbol in allowed_symbol_set]
    rejected_symbols = [symbol for symbol in canonical_symbols if symbol not in allowed_symbol_set]
    benchmarks = _benchmarks_for_market(market, allowed_symbols)
    if canonical_symbols:
        if rejected_symbols:
            return _decision(
                "block",
                market,
                benchmarks,
                "tool_symbol_not_in_benchmark_universe",
                warnings=[
                    "Benchmark policy only allows documented benchmark symbols for explicit market-wide prompts.",
                    "Do not treat a single stock or ETF outside the benchmark universe as a system benchmark.",
                ],
                metadata={
                    "tool_name": tool or None,
                    "requested_symbols": canonical_symbols,
                    "allowed_symbols": allowed_symbols,
                    "rejected_symbols": rejected_symbols,
                    "benchmark_universe": universe_symbols,
                },
            )
    else:
        allowed_symbols = universe_symbols
        benchmarks = _benchmarks_for_market(market, allowed_symbols)

    return _decision(
        "allow_benchmark",
        market,
        benchmarks,
        f"explicit_{market}_market_wide_intent",
        warnings=["Benchmark policy does not bypass asset-type routing or data freshness checks."],
        metadata={
            "tool_name": tool or None,
            "requested_symbols": canonical_symbols,
            "allowed_symbols": allowed_symbols,
            "rejected_symbols": [],
            "benchmark_universe": universe_symbols,
        },
    )


def _decision(
    decision: str,
    market: str | None,
    benchmarks: list[dict[str, str]],
    reason: str,
    *,
    warnings: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_metadata = {
        "benchmark_policy": True,
        "source": "system_selected_benchmark",
    }
    if metadata:
        base_metadata.update(metadata)
    return {
        "decision": decision,
        "market": market,
        "benchmarks": [dict(item) for item in benchmarks],
        "reason": reason,
        "warnings": warnings or [],
        "metadata": base_metadata,
    }


def _benchmarks_for_market(market: str, symbols: list[str]) -> list[dict[str, str]]:
    universe = BENCHMARKS_BY_MARKET.get(market, [])
    if not symbols:
        return [dict(item) for item in universe]
    wanted = set(symbols)
    return [dict(item) for item in universe if item["symbol"] in wanted]


def _benchmark_symbols_for_market(market: str) -> list[str]:
    return [item["symbol"] for item in BENCHMARKS_BY_MARKET.get(market, [])]


def _no_symbol_market_wide_tool(tool_name: str, args: dict[str, Any]) -> dict[str, str] | None:
    tool = tool_name.strip().lower()
    symbols = _extract_symbols_from_args(args)
    if tool == "get_stock_news" and not symbols:
        for key in ("scope", "mode"):
            value = str(args.get(key) or "").strip().lower()
            if value in _NO_SYMBOL_GLOBAL_NEWS_MODES:
                return {
                    "reason": "no_symbol_global_news_tool_allowed",
                    "metadata_key": "no_symbol_global_tool_allowed",
                }
    if tool == "get_sector_info" and not symbols:
        value = str(args.get("mode") or "").strip().lower()
        if value in _NO_SYMBOL_SECTOR_MODES:
            return {
                "reason": "sector_ranking_no_symbol_allowed",
                "metadata_key": "sector_ranking_no_symbol_allowed",
            }
    return None


def _detect_market(prompt: str) -> str | None:
    compact = _compact(prompt)
    lower = prompt.lower()
    if any(token in compact for token in ("a股", "沪深", "中国股市", "内地股市")):
        return "cn"
    if any(token in lower for token in ("china a-share", "a-share market", "a share market")):
        return "cn"
    if any(token in compact for token in ("美股", "美国股市", "纳斯达克", "道指", "标普")):
        return "us"
    if any(token in lower for token in ("us market", "u.s. market", "nasdaq", "s&p", "dow")):
        return "us"
    if any(token in compact for token in ("港股", "香港股市")):
        return "hk"
    if "hong kong market" in lower:
        return "hk"
    return None


def _has_market_wide_intent(prompt: str) -> bool:
    compact = _compact(prompt)
    lower = prompt.lower()
    chinese_hints = (
        "市场",
        "大盘",
        "整体",
        "全市场",
        "指数",
        "板块",
        "行业",
        "宏观",
        "风险",
        "今日市场",
        "今天怎么样",
        "怎么样",
        "表现如何",
    )
    english_hints = (
        "market",
        "overall",
        "broad market",
        "sector",
        "industry",
        "macro",
        "risk",
        "today",
    )
    return any(token in compact for token in chinese_hints) or any(token in lower for token in english_hints)


def _is_ambiguous_market_prompt(prompt: str) -> bool:
    compact = _compact(prompt)
    lower = prompt.lower()
    ambiguous_cn = ("看看市场", "最近怎么样", "有什么机会", "哪些能买", "帮我看看")
    ambiguous_en = ("market update", "opportunities")
    return any(token in compact for token in ambiguous_cn) or any(token in lower for token in ambiguous_en)


def _is_user_specified_target(prompt: str) -> bool:
    compact = _compact(prompt)
    upper = prompt.upper()
    lower = prompt.lower()

    if re.search(r"(?<![\w.])(?:\d{6}\.(?:SH|SZ|BJ)|\d{1,5}\.HK|[A-Z]{1,5}\.US)(?![\w.])", upper):
        return True
    if any(name in prompt for name in _KNOWN_CHINESE_TARGETS):
        return True
    if re.search(r"(?<![\w.])\d{4,6}(?![\w.])", upper):
        return True
    if any(word in lower.split() for word in _KNOWN_SINGLE_TARGET_WORDS):
        return True
    if "etf" in lower and not _detect_market(prompt):
        return True
    if compact in {"腾讯", "贵州茅台", "平安银行"}:
        return True
    return False


def _extract_symbols_from_args(args: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for key in ("codes", "symbols", "symbol", "ticker", "tickers", "code"):
        if key not in args:
            continue
        value = args.get(key)
        if isinstance(value, str):
            symbols.extend(_extract_symbols(value))
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                symbols.extend(_extract_symbols(str(item)))
    return _unique(symbols)


def _extract_symbols(value: str) -> list[str]:
    text = value.upper()
    out: list[str] = []
    for part in re.split(r"[,;，；\s]+", text):
        token = part.strip()
        if not token:
            continue
        if re.fullmatch(r"(?:\d{6}\.(?:SH|SZ|BJ)|\d{1,5}\.HK|[A-Z]{1,5}\.US)", token):
            out.append(token)
        elif re.fullmatch(r"[A-Z]{1,5}", token):
            out.append(token)
    return out


def _canonicalize_symbols_for_market(symbols: list[str], market: str | None) -> list[str]:
    out: list[str] = []
    for symbol in symbols:
        upper = str(symbol).strip().upper()
        if not upper:
            continue
        if market == "us" and re.fullmatch(r"[A-Z]{1,5}", upper):
            out.append(f"{upper}.US")
        else:
            out.append(upper)
    return _unique(out)


def _compact(prompt: str) -> str:
    return re.sub(r"\s+", "", str(prompt or "").lower())


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
