"""Pure asset-type-aware tool routing guard.

This module contains no provider calls, tool execution, LLM calls, or file I/O.
It only evaluates whether a proposed tool is compatible with a known market and
asset type.
"""

from __future__ import annotations

from typing import Any


_SUPPORTED_TOOLS = {
    "get_market_data",
    "get_sector_info",
    "get_financial_statements",
    "get_shareholder_count",
    "get_margin_trading",
    "get_block_trades",
    "get_stock_news",
    "web_search",
    "read_url",
    "search_symbol",
}
_DISCOVERY_OR_WEB_TOOLS = {"web_search", "read_url", "search_symbol"}
_SOURCE_TYPES = {
    "web_search": "web_unstructured",
    "read_url": "web_unstructured",
    "search_symbol": "discovery",
}
_STOCK_SPECIFIC_TOOLS = {
    "get_sector_info",
    "get_financial_statements",
    "get_shareholder_count",
    "get_margin_trading",
    "get_block_trades",
}
_CN_MARKETS = {"cn", "a_share", "ashare", "china_a", "china a", "a-share"}
_VALID_DECISIONS = {"allow", "warn", "block", "skip", "ask_for_confirmation"}


def evaluate_tool_asset_compatibility(
    tool_name: str,
    symbol: str | None = None,
    market: str | None = None,
    asset_type: str | None = None,
    original_prompt: str | None = None,
) -> dict[str, Any]:
    """Evaluate whether a tool is compatible with a symbol's asset type.

    Args:
        tool_name: Proposed tool name.
        symbol: Proposed symbol, when the tool call has one.
        market: Market hint such as ``CN``, ``US``, ``HK`` or ``a_share``.
        asset_type: Asset type hint such as ``stock``, ``index``, ``etf``.
        original_prompt: Reserved for future prompt-aware policy.

    Returns:
        JSON-serializable routing decision.
    """
    del original_prompt  # Reserved for future policy.

    tool = _normalize_token(tool_name)
    normalized_market = _normalize_market(market)
    normalized_asset = _normalize_asset_type(asset_type)

    if tool not in _SUPPORTED_TOOLS:
        return _decision(
            "allow",
            "unsupported_tool_for_mvp",
            "unsupported_tool_for_mvp",
            tool_name=tool_name,
            symbol=symbol,
            market=normalized_market,
            asset_type=normalized_asset,
            guarded=False,
        )

    if tool in _DISCOVERY_OR_WEB_TOOLS:
        return _decision(
            "allow",
            f"{tool} is a discovery or unstructured-source tool and is not asset-type blocked.",
            "discovery_or_web_tool",
            tool_name=tool_name,
            symbol=symbol,
            market=normalized_market,
            asset_type=normalized_asset,
            source_type=_SOURCE_TYPES[tool],
        )

    if normalized_asset == "unknown":
        return _unknown_asset_decision(tool, tool_name, symbol, normalized_market)

    if tool == "get_market_data":
        if normalized_asset in {"stock", "index", "etf"}:
            return _decision("allow", "market data supports broad listed instruments", "market_data_broad_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        return _decision("warn", "market data may support this asset type, but compatibility is not confirmed", "market_data_uncertain_asset", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=[f"Confirm provider support before treating {normalized_asset} market data as complete."])

    if tool == "get_sector_info":
        if normalized_asset == "stock":
            return _decision("allow", "sector membership is designed for stocks", "sector_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        return _decision("block", "sector membership is stock-specific and should not be used for this asset type", "sector_non_stock_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=[f"Use market-wide sector ranking or a different tool for {normalized_asset}."])

    if tool == "get_financial_statements":
        if normalized_asset == "stock":
            return _decision("allow", "financial statements are company-specific", "financials_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        return _decision("block", "financial statements are company-specific and unsupported for this asset type", "financials_non_stock_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)

    if tool == "get_shareholder_count":
        if normalized_asset == "stock":
            return _decision("allow", "shareholder count is a company disclosure", "shareholder_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        return _decision("block", "shareholder count is a company disclosure and unsupported for this asset type", "shareholder_non_stock_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)

    if tool == "get_margin_trading":
        if normalized_asset == "index":
            return _decision("block", "margin trading balances are security-specific, not index-level", "margin_index_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        if normalized_asset == "etf":
            return _decision("warn", "some A-share ETFs may have margin data, but provider semantics must be confirmed", "margin_etf_warn", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=["Do not treat ETF margin data as company-level leverage or fund-flow data."])
        if normalized_asset == "stock":
            if _is_cn_market(normalized_market):
                return _decision("allow", "A-share stock margin trading is supported by the current tool", "margin_a_share_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
            return _decision("warn", "margin trading tool is A-share focused; non-A-share stock support is not confirmed", "margin_non_a_share_stock_warn", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=["Confirm market support before using margin-trading output."])
        return _decision("block", "margin trading is unsupported for this asset type", "margin_unsupported_asset_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)

    if tool == "get_block_trades":
        if normalized_asset == "stock":
            return _decision("allow", "block trades are security-specific and valid for stock symbols", "block_trades_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        if normalized_asset == "etf":
            return _decision("warn", "ETF block-trade semantics may differ from stock block trades", "block_trades_etf_warn", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=["Confirm provider support before using ETF block-trade data."])
        return _decision("block", "block trades are security-specific and unsupported for this asset type", "block_trades_non_stock_block", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)

    if tool == "get_stock_news":
        if normalized_asset == "stock":
            return _decision("allow", "stock news is suitable for stock symbols", "stock_news_stock_allow", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset)
        return _decision("warn", "news may be available, but source semantics differ for this asset type", "stock_news_non_stock_warn", tool_name=tool_name, symbol=symbol, market=normalized_market, asset_type=normalized_asset, warnings=[f"Label news for {normalized_asset} as source-dependent, not company-specific coverage."])

    return _decision(
        "allow",
        "tool is supported by MVP but has no restrictive rule",
        "default_supported_allow",
        tool_name=tool_name,
        symbol=symbol,
        market=normalized_market,
        asset_type=normalized_asset,
    )


def _unknown_asset_decision(tool: str, tool_name: str, symbol: str | None, market: str | None) -> dict[str, Any]:
    if tool in _STOCK_SPECIFIC_TOOLS:
        return _decision(
            "ask_for_confirmation",
            "asset type is unknown for a stock-specific tool",
            "unknown_asset_stock_specific_confirm",
            tool_name=tool_name,
            symbol=symbol,
            market=market,
            asset_type="unknown",
            warnings=["Ask the user or a symbol resolver to confirm whether this is a stock, index, ETF, fund, or other asset."],
        )
    return _decision(
        "warn",
        "asset type is unknown; tool can proceed only with disclosure",
        "unknown_asset_warn",
        tool_name=tool_name,
        symbol=symbol,
        market=market,
        asset_type="unknown",
        warnings=["Asset type is unknown; disclose this uncertainty in the report."],
    )


def _decision(
    decision: str,
    reason: str,
    matched_rule: str,
    *,
    tool_name: str,
    symbol: str | None,
    market: str | None,
    asset_type: str | None,
    warnings: list[str] | None = None,
    guarded: bool = True,
    source_type: str | None = None,
) -> dict[str, Any]:
    if decision not in _VALID_DECISIONS:
        raise ValueError(f"invalid routing decision: {decision}")
    metadata: dict[str, Any] = {
        "guarded": guarded,
        "guard_type": "asset_type_tool_routing",
    }
    if source_type:
        metadata["source_type"] = source_type
    return {
        "decision": decision,
        "reason": reason,
        "tool_name": tool_name,
        "symbol": symbol,
        "market": market,
        "asset_type": asset_type or "unknown",
        "matched_rule": matched_rule,
        "warnings": warnings or [],
        "metadata": metadata,
    }


def _normalize_token(value: str | None) -> str:
    return str(value or "").strip().lower()


def _normalize_asset_type(value: str | None) -> str:
    raw = _normalize_token(value)
    if raw in {"", "none", "null"}:
        return "unknown"
    if raw in {"etf", "exchange_traded_fund", "exchange-traded-fund"}:
        return "etf"
    if raw in {"stock", "equity", "company"}:
        return "stock"
    if raw in {"index", "indice", "benchmark"}:
        return "index"
    if raw in {"fund", "mutual_fund", "mutual-fund"}:
        return "fund"
    return raw


def _normalize_market(value: str | None) -> str | None:
    raw = _normalize_token(value)
    if raw in {"", "none", "null"}:
        return None
    if raw in _CN_MARKETS:
        return "cn"
    if raw in {"us", "usa", "united_states", "united states"}:
        return "us"
    if raw in {"hk", "hong_kong", "hong kong"}:
        return "hk"
    return raw


def _is_cn_market(market: str | None) -> bool:
    return market == "cn"

