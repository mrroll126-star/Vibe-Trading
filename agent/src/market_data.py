"""Shared market data helpers for MCP and local agent tools."""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.data_quality import assess_freshness
from src.symbols import NormalizedSymbol, normalize_symbol
from src.symbols.config import is_symbol_normalizer_enabled

logger = logging.getLogger(__name__)

DEFAULT_MAX_ROWS = 250

# Symbol -> preferred source. The matched source is the head of its market's
# fallback chain (registry.FALLBACK_CHAINS), so an unavailable preferred source
# still degrades gracefully to the rest of the chain. US/HK equities route to
# the throttle-tolerant Yahoo public endpoint first (lower IP-ban risk than the
# yfinance SDK), A-shares to the Tencent quote endpoint.
_SOURCE_PATTERNS = [
    (re.compile(r"^local:", re.I), "local"),
    (re.compile(r"^\d{6}\.(SZ|SH|BJ)$", re.I), "tencent"),
    (re.compile(r"^[A-Z]+\.US$", re.I), "yahoo"),
    (re.compile(r"^\d{3,5}\.HK$", re.I), "yahoo"),
    (re.compile(r"^[A-Z]+-USDT$", re.I), "okx"),
    (re.compile(r"^[A-Z]+/USDT$", re.I), "ccxt"),
]


def detect_source(code: str) -> str:
    """Infer the best loader source for a normalized symbol."""
    for pattern, source in _SOURCE_PATTERNS:
        if pattern.match(code):
            return source
    return "tushare"


def get_loader(source: str):
    """Get loader class via registry with fallback support."""
    from backtest.loaders.registry import get_loader_cls_with_fallback

    return get_loader_cls_with_fallback(source)


def cap_rows(records: list, max_rows: int) -> list | dict[str, object]:
    """Bound a per-symbol row list to keep tool payloads within budget."""
    n = len(records)
    if max_rows < 0:
        max_rows = DEFAULT_MAX_ROWS
    if max_rows == 0 or n <= max_rows:
        return records
    step = math.ceil(n / max_rows)
    sampled = records[::step]
    if sampled[-1] is not records[-1]:
        sampled = sampled + [records[-1]]
    return {
        "rows": n,
        "returned": len(sampled),
        "truncated": True,
        "policy": f"every-{step}th-row (even stride; last bar pinned)",
        "hint": "narrow the date range, coarsen interval, or set max_rows=0 for all rows",
        "data": sampled,
    }


def _json_safe(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def fetch_market_data(
    *,
    codes: list[str],
    start_date: str,
    end_date: str,
    source: str = "auto",
    interval: str = "1D",
    max_rows: int = DEFAULT_MAX_ROWS,
    loader_resolver: Callable[[str], type] = get_loader,
) -> dict[str, Any]:
    """Fetch normalized OHLCV data through the repository loader layer."""
    results: dict[str, Any] = {}
    data_quality: dict[str, Any] = {}
    requested_at = datetime.now().astimezone()
    requested_date_text = requested_at.date().isoformat()
    time_sensitive = end_date == requested_date_text

    query_codes, raw_inputs_by_code, normalization_meta, blocked_codes = _prepare_market_data_codes(codes)
    if normalization_meta:
        results["_symbol_normalization"] = normalization_meta
    if blocked_codes:
        results["_unresolved"] = blocked_codes
        for blocked in blocked_codes:
            meta = normalization_meta.get(blocked, {}) if isinstance(normalization_meta, dict) else {}
            warning = "; ".join(meta.get("warnings") or []) or "symbol normalization did not produce a callable symbol"
            data_quality[blocked] = assess_freshness(
                [],
                tool_name="get_market_data",
                raw_input=blocked,
                normalized_symbol=meta.get("normalized_symbol"),
                provider=None,
                requested_at=requested_at,
                interval=interval,
                time_sensitive=time_sensitive,
                source_error=warning,
            ).to_dict()

    if source == "auto":
        groups: dict[str, list[str]] = {}
        for code in query_codes:
            src = detect_source(code)
            groups.setdefault(src, []).append(code)
    else:
        groups = {source: list(query_codes)}

    for src, src_codes in groups.items():
        loader_cls = loader_resolver(src)
        loader = loader_cls()
        loader_error: str | None = None
        try:
            data_map = loader.fetch(src_codes, start_date, end_date, interval=interval)
        except Exception as exc:
            logger.exception(
                "market-data loader %r failed for %s; codes fall through to _unresolved",
                src,
                src_codes,
            )
            loader_error = str(exc)
            data_map = {}
        for symbol, df in data_map.items():
            records = df.reset_index().to_dict(orient="records")
            for row in records:
                for key, value in row.items():
                    row[key] = _json_safe(value)
            capped = cap_rows(records, max_rows)
            results[symbol] = capped
            data_quality[symbol] = assess_freshness(
                capped,
                tool_name="get_market_data",
                raw_input=raw_inputs_by_code.get(symbol, symbol),
                normalized_symbol=symbol,
                provider=src,
                requested_at=requested_at,
                interval=interval,
                time_sensitive=time_sensitive,
            ).to_dict()
        if loader_error:
            for code in src_codes:
                if code not in results:
                    data_quality[code] = assess_freshness(
                        [],
                        tool_name="get_market_data",
                        raw_input=raw_inputs_by_code.get(code, code),
                        normalized_symbol=code,
                        provider=src,
                        requested_at=requested_at,
                        interval=interval,
                        time_sensitive=time_sensitive,
                        source_error=loader_error,
                    ).to_dict()

    unresolved = [code for code in query_codes if code not in results]
    if unresolved:
        existing_unresolved = results.get("_unresolved")
        if isinstance(existing_unresolved, list):
            results["_unresolved"] = existing_unresolved + unresolved
        else:
            results["_unresolved"] = unresolved
        for code in unresolved:
            if code not in data_quality:
                provider = detect_source(code) if source == "auto" else source
                data_quality[code] = assess_freshness(
                    [],
                    tool_name="get_market_data",
                    raw_input=raw_inputs_by_code.get(code, code),
                    normalized_symbol=code,
                    provider=provider,
                    requested_at=requested_at,
                    interval=interval,
                    time_sensitive=time_sensitive,
                ).to_dict()

    if data_quality:
        results["_data_quality"] = data_quality

    return results


def fetch_market_data_json(**kwargs: Any) -> str:
    """Fetch market data and return strict JSON."""
    return json.dumps(fetch_market_data(**kwargs), ensure_ascii=False, indent=2, allow_nan=False)


def _prepare_market_data_codes(codes: list[str]) -> tuple[list[str], dict[str, str], dict[str, Any], list[str]]:
    if not is_symbol_normalizer_enabled():
        return list(codes), {code: code for code in codes}, {}, []

    query_codes: list[str] = []
    raw_inputs_by_code: dict[str, str] = {}
    normalization_meta: dict[str, Any] = {}
    blocked_codes: list[str] = []

    for code in codes:
        raw = str(code)
        pass_through = _normalizer_pass_through(raw)
        if pass_through:
            query_codes.append(raw)
            raw_inputs_by_code[raw] = raw
            normalization_meta[raw] = {
                "raw_input": raw,
                "normalized_symbol": raw,
                "market": None,
                "exchange": None,
                "asset_type": None,
                "needs_confirmation": False,
                "warnings": [],
                "source": "pass_through",
            }
            continue

        normalized = normalize_symbol(raw)
        meta = normalized.to_dict()
        normalization_meta[raw] = meta

        if _should_block_normalized_symbol(raw, normalized):
            blocked_codes.append(raw)
            continue

        normalized_symbol = normalized.normalized_symbol
        if normalized_symbol:
            query_codes.append(normalized_symbol)
            raw_inputs_by_code[normalized_symbol] = raw
        else:
            blocked_codes.append(raw)

    return query_codes, raw_inputs_by_code, normalization_meta, blocked_codes


def _normalizer_pass_through(raw: str) -> bool:
    upper = raw.strip().upper()
    return upper.startswith("LOCAL:") or upper.endswith("-USDT") or upper.endswith("/USDT")


def _should_block_normalized_symbol(raw: str, normalized: NormalizedSymbol) -> bool:
    if not normalized.normalized_symbol:
        return True
    if not normalized.needs_confirmation:
        return False
    return not _is_explicit_symbol(raw)


def _is_explicit_symbol(raw: str) -> bool:
    upper = raw.strip().upper()
    return bool(
        re.fullmatch(r"\d{6}\.(SH|SZ|BJ)", upper)
        or re.fullmatch(r"[A-Z]{1,10}\.US", upper)
        or re.fullmatch(r"\d{1,5}\.HK", upper)
        or re.fullmatch(r"(SH|SZ)\.?\d{6}", upper)
        or re.fullmatch(r"HK\.?\d{1,5}", upper)
    )
