"""Mock-first hooks for the optional a-stock-data financial adapter.

This module is intentionally conservative.  It does not call the network,
import vendor code, read files, or install dependencies.  The fetch function is
a stable seam for tests and a future live adapter implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from src.symbols.normalizer import normalize_symbol


_A_SHARE_INDEX_SYMBOLS = {
    "000001.SH",
    "399001.SZ",
    "399006.SZ",
    "000300.SH",
    "000688.SH",
}
_A_SHARE_ETF_SYMBOLS = {
    "510300.SH",
    "159915.SZ",
}


def fetch_a_stock_financials(
    symbol: str,
    statement_type: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return an explicit unavailable payload until live fetching is approved.

    Args:
        symbol: Confirmed A-share stock symbol.
        statement_type: Optional statement selector.
        **kwargs: Reserved for a future live implementation.

    Returns:
        A dict that normalizes to a missing-data result.
    """

    del kwargs
    return {
        "ok": False,
        "error": "a_stock_data_live_fetch_not_implemented",
        "data": [],
        "source": "a_stock_data",
        "upstream": "not_implemented",
        "statement_type": statement_type,
        "symbol": symbol,
    }


def is_a_stock_financials_fallback_eligible(
    symbol: str,
    market: str | None = None,
    asset_type: str | None = None,
) -> dict[str, Any]:
    """Evaluate whether the financial fallback may run for a symbol.

    This is an internal safety fuse.  The AgentLoop guards should already have
    run, but the adapter still refuses ambiguous, non-A-share, index, and ETF
    inputs on its own.
    """

    raw_symbol = "" if symbol is None else str(symbol).strip()
    normalized_input = normalize_symbol(raw_symbol)
    normalized_symbol = (
        normalized_input.normalized_symbol.upper()
        if normalized_input.normalized_symbol
        else raw_symbol.upper()
    )
    normalized_market = _normalize_market(market) or _market_from_symbol(normalized_symbol)
    normalized_asset = _normalize_asset_type(asset_type) or normalized_input.asset_type or "unknown"

    result = {
        "eligible": False,
        "reason": "",
        "symbol": normalized_symbol,
        "market": normalized_market,
        "asset_type": normalized_asset,
    }

    if not raw_symbol:
        result["reason"] = "empty_symbol"
        return result
    if normalized_symbol in _A_SHARE_INDEX_SYMBOLS:
        result["asset_type"] = "index"
        result["reason"] = "index_not_eligible_for_company_financials"
        return result
    if normalized_symbol in _A_SHARE_ETF_SYMBOLS:
        result["asset_type"] = "etf"
        result["reason"] = "etf_not_eligible_for_company_financials"
        return result
    explicit_suffixed_a_share = bool(re.fullmatch(r"\d{6}\.(SH|SZ)", raw_symbol.upper()))
    if (
        normalized_input.needs_confirmation
        and not explicit_suffixed_a_share
    ) or normalized_input.normalized_symbol is None:
        result["reason"] = "symbol_requires_confirmation_or_is_invalid"
        return result
    if normalized_market != "a_share":
        result["reason"] = "not_a_share_market"
        return result
    if not (normalized_symbol.endswith(".SH") or normalized_symbol.endswith(".SZ")):
        result["reason"] = "symbol_must_be_explicit_sh_or_sz"
        return result
    if normalized_asset != "stock":
        result["reason"] = "asset_type_not_stock"
        return result

    result["eligible"] = True
    result["reason"] = "eligible_a_share_stock"
    return result


def should_try_a_stock_financials_fallback(primary_result: dict[str, Any] | None) -> bool:
    """Return whether a primary financial result is missing enough to fallback."""

    if primary_result is None:
        return True
    if not isinstance(primary_result, Mapping):
        return True
    if primary_result.get("ok") is False:
        return True
    if primary_result.get("error"):
        return True
    if _quality_status_is_missing(primary_result):
        return True
    if _has_unavailable_marker(primary_result):
        return True
    if not _has_financial_rows(primary_result):
        return True
    return False


def _normalize_market(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    if raw in {"a_share", "ashare", "cn", "china_a", "china a", "a-share"}:
        return "a_share"
    if raw in {"us", "usa"}:
        return "us"
    if raw in {"hk", "hong_kong", "hong kong"}:
        return "hk"
    return None


def _normalize_asset_type(value: str | None) -> str | None:
    raw = str(value or "").strip().lower()
    if raw in {"stock", "equity", "company"}:
        return "stock"
    if raw in {"index", "benchmark"}:
        return "index"
    if raw in {"etf", "exchange_traded_fund", "exchange-traded-fund"}:
        return "etf"
    if raw:
        return raw
    return None


def _market_from_symbol(symbol: str) -> str | None:
    if symbol.endswith((".SH", ".SZ", ".BJ")):
        return "a_share"
    if symbol.endswith(".US"):
        return "us"
    if symbol.endswith(".HK"):
        return "hk"
    return None


def _quality_status_is_missing(result: Mapping[str, Any]) -> bool:
    data_quality = result.get("_data_quality")
    if not isinstance(data_quality, Mapping):
        return False
    for meta in data_quality.values():
        if not isinstance(meta, Mapping):
            continue
        status = str(meta.get("status") or meta.get("freshness_status") or "").lower()
        if status == "missing":
            return True
    return False


def _has_unavailable_marker(result: Mapping[str, Any]) -> bool:
    text_values = [
        result.get("status"),
        result.get("reason"),
        result.get("error_code"),
        result.get("error"),
    ]
    haystack = " ".join(str(value).lower() for value in text_values if value)
    return any(marker in haystack for marker in ("unsupported", "unavailable", "not_implemented"))


def _has_financial_rows(result: Mapping[str, Any]) -> bool:
    data = result.get("data")
    if isinstance(data, Mapping):
        for value in data.values():
            if _payload_has_rows(value):
                return True
        return False
    return _payload_has_rows(data) or _payload_has_rows(result.get("rows")) or _payload_has_rows(result.get("periods"))


def _payload_has_rows(payload: Any) -> bool:
    if isinstance(payload, list):
        return len(payload) > 0
    if isinstance(payload, Mapping):
        for key in ("periods", "rows", "data", "items", "result"):
            if key in payload and _payload_has_rows(payload.get(key)):
                return True
    return False
