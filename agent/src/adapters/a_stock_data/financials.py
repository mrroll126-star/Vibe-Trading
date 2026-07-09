"""Optional a-stock-data financial adapter hooks.

This module stays behind ``VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER`` at the
tool layer.  It does not import vendor code, read files, or add dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import requests

from src.symbols.normalizer import normalize_symbol


SINA_FINANCIAL_URL = (
    "https://quotes.sina.cn/cn/api/openapi.php/"
    "CompanyFinanceService.getFinanceReport2022"
)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
STATEMENT_TO_SINA = {
    "income": "lrb",
    "balance": "fzb",
    "cashflow": "llb",
}
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
    """Fetch A-share financial statement rows from the approved Sina candidate.

    Args:
        symbol: Confirmed A-share stock symbol.
        statement_type: ``income``, ``balance``, or ``cashflow``.
        **kwargs: Optional ``timeout`` and ``num``.

    Returns:
        A raw payload designed for ``normalize_a_stock_financials_result``.
    """

    statement = str(statement_type or "income").strip().lower()
    report_type = STATEMENT_TO_SINA.get(statement)
    if report_type is None:
        return _unavailable_payload(
            symbol,
            statement,
            f"unsupported_statement_type_for_sina_financials: {statement}",
        )

    code, error = _symbol_to_sina_code(symbol)
    if error:
        return _unavailable_payload(symbol, statement, error)

    timeout = float(kwargs.get("timeout", 15))
    num = int(kwargs.get("num", 8))
    prefix = "sh" if code.startswith("6") else "sz"
    params = {
        "paperCode": f"{prefix}{code}",
        "source": report_type,
        "type": "0",
        "page": "1",
        "num": str(num),
    }

    try:
        response = requests.get(
            SINA_FINANCIAL_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        rows = _parse_sina_financial_rows(payload, num=num)
    except Exception as exc:  # noqa: BLE001 - fallback must report, not crash
        return _unavailable_payload(
            symbol,
            statement,
            f"sina_financial_report_request_failed: {type(exc).__name__}: {exc}",
        )

    return {
        "ok": bool(rows),
        "data": rows,
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "statement_type": statement,
        "symbol": symbol,
        "error": None if rows else "sina_financial_report_returned_no_rows",
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


def _symbol_to_sina_code(symbol: str) -> tuple[str, str | None]:
    cleaned = str(symbol or "").strip().upper()
    if not cleaned:
        return "", "empty_symbol"
    if not (cleaned.endswith(".SH") or cleaned.endswith(".SZ")):
        return "", "symbol_must_be_explicit_sh_or_sz"
    digits = cleaned.split(".", 1)[0]
    if not (len(digits) == 6 and digits.isdigit()):
        return "", "symbol_must_start_with_six_digits"
    return digits, None


def _parse_sina_financial_rows(payload: Mapping[str, Any], *, num: int) -> list[dict[str, Any]]:
    report_list = (
        payload.get("result", {})
        .get("data", {})
        .get("report_list", {})
        or {}
    )
    if not isinstance(report_list, Mapping):
        return []

    rows: list[dict[str, Any]] = []
    for period in sorted(report_list.keys(), reverse=True)[:num]:
        obj = report_list.get(period) or {}
        items = obj.get("data", []) if isinstance(obj, Mapping) else []
        rec = {"报告期": _format_period(str(period))}
        for item in items or []:
            if not isinstance(item, Mapping):
                continue
            title = item.get("item_title", "")
            if not title or item.get("item_value") is None:
                continue
            rec[str(title)] = item.get("item_value")
            tongbi = item.get("item_tongbi")
            if tongbi not in (None, ""):
                rec[f"{title}_同比"] = tongbi
        rows.append(rec)
    return rows


def _format_period(period: str) -> str:
    if len(period) >= 8 and period[:8].isdigit():
        return f"{period[:4]}-{period[4:6]}-{period[6:8]}"
    return period


def _unavailable_payload(symbol: str, statement_type: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "data": [],
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "statement_type": statement_type,
        "symbol": symbol,
    }


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
