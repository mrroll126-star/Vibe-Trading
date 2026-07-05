"""Rule-based symbol normalization helper.

This module is deliberately pure: it performs no network requests, does not
call market-data providers, and is not wired into existing tool behavior yet.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


_US_ETFS = {"QQQ", "SPY"}
_CN_AMBIGUOUS = {"000001"}
_COMMON_HK_CODES = {"700", "0700", "00700", "9988", "09988"}

_SH_STOCK_PREFIXES = ("600", "601", "603", "605", "688")
_SZ_STOCK_PREFIXES = ("000", "001", "002", "003", "300", "301")
_SH_ETF_PREFIXES = ("510", "511", "512", "513", "515", "516", "518")
_SZ_ETF_PREFIXES = ("159",)


@dataclass(frozen=True)
class NormalizedSymbol:
    """Structured result from a normalization attempt."""

    raw_input: str
    normalized_symbol: str | None
    market: str | None
    exchange: str | None
    asset_type: str | None
    name: str | None = None
    confidence: float = 0.0
    needs_confirmation: bool = False
    candidate_symbols: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source: str = "rule"

    @property
    def is_valid(self) -> bool:
        """Return whether a primary normalized symbol was produced."""
        return bool(self.normalized_symbol)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


def normalize_symbol(raw: str, context: dict[str, Any] | None = None) -> NormalizedSymbol:
    """Normalize a user-entered symbol into the project convention.

    Args:
        raw: User input such as ``"SPY"``, ``"600519"`` or ``"00700.HK"``.
        context: Optional hints. Supported keys: ``market``, ``exchange``,
            ``asset_type``, ``name_hint`` and ``prefer_index``.

    Returns:
        A structured normalization result. Invalid or ambiguous inputs return
        ``normalized_symbol=None`` with warnings rather than raising.
    """
    ctx = context or {}
    raw_input = "" if raw is None else str(raw)
    cleaned = raw_input.strip()
    if not cleaned:
        return _invalid(raw_input, "empty symbol input")

    if _contains_cjk(cleaned):
        return NormalizedSymbol(
            raw_input=raw_input,
            normalized_symbol=None,
            market=None,
            exchange=None,
            asset_type=None,
            name=cleaned,
            confidence=0.0,
            needs_confirmation=True,
            warnings=["Chinese name resolution requires a future security master table."],
            source="name_pending",
        )

    upper = cleaned.upper()
    context_market = str(ctx.get("market") or "").strip().upper()
    context_exchange = str(ctx.get("exchange") or "").strip().upper()
    prefer_index = bool(ctx.get("prefer_index")) or context_market == "INDEX"

    # Explicit exchange-prefix forms for A-shares and HK.
    prefixed = _normalize_exchange_prefix(upper, raw_input)
    if prefixed is not None:
        return prefixed

    # Already-suffixed forms.
    suffixed = _normalize_suffixed(upper, raw_input)
    if suffixed is not None:
        return suffixed

    # Six-digit numeric symbols are A-share candidates before any HK logic.
    if re.fullmatch(r"\d{6}", upper):
        return _normalize_a_share_digits(upper, raw_input, prefer_index)

    # Pure letters: US ticker by default, up to 5 characters.
    if re.fullmatch(r"[A-Z]+", upper):
        if len(upper) <= 5:
            return _us_result(raw_input, upper)
        return _invalid(raw_input, f"letter-only ticker is too long for default US rule: {upper}")

    # One-to-five digit codes can be HK only with context or known common HK examples.
    if re.fullmatch(r"\d{1,5}", upper):
        hk_context = context_market == "HK" or context_exchange == "HK"
        if upper in _COMMON_HK_CODES or hk_context:
            return _hk_result(raw_input, upper, needs_confirmation=not hk_context and upper not in _COMMON_HK_CODES)
        candidate = _format_hk(upper)
        return NormalizedSymbol(
            raw_input=raw_input,
            normalized_symbol=None,
            market="HK",
            exchange="HK",
            asset_type="stock",
            confidence=0.35,
            needs_confirmation=True,
            candidate_symbols=[candidate],
            warnings=[f"numeric code {upper!r} is ambiguous without market context; candidate: {candidate}"],
            source="rule_candidate",
        )

    return _invalid(raw_input, f"unrecognized symbol format: {cleaned}")


def normalize_many(inputs: list[str], context: dict[str, Any] | None = None) -> list[NormalizedSymbol]:
    """Normalize a list of raw inputs with the same optional context."""
    return [normalize_symbol(item, context=context) for item in inputs]


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def _invalid(raw_input: str, warning: str) -> NormalizedSymbol:
    return NormalizedSymbol(
        raw_input=raw_input,
        normalized_symbol=None,
        market=None,
        exchange=None,
        asset_type=None,
        confidence=0.0,
        needs_confirmation=False,
        warnings=[warning],
        source="invalid",
    )


def _normalize_exchange_prefix(upper: str, raw_input: str) -> NormalizedSymbol | None:
    match = re.fullmatch(r"(SH|SZ)(?:\.)?(\d{6})", upper)
    if match:
        exchange, digits = match.groups()
        return _cn_result(raw_input, digits, exchange)

    match = re.fullmatch(r"HK(?:\.)?(\d{1,5})", upper)
    if match:
        return _hk_result(raw_input, match.group(1), needs_confirmation=False)

    return None


def _normalize_suffixed(upper: str, raw_input: str) -> NormalizedSymbol | None:
    match = re.fullmatch(r"([A-Z]{1,10})\.US", upper)
    if match:
        ticker = match.group(1)
        if len(ticker) > 5:
            return _invalid(raw_input, f"US ticker is too long for default rule: {ticker}")
        return _us_result(raw_input, ticker)

    match = re.fullmatch(r"(\d{6})\.(SH|SZ)", upper)
    if match:
        digits, exchange = match.groups()
        return _cn_result(raw_input, digits, exchange)

    match = re.fullmatch(r"(\d{1,5})\.HK", upper)
    if match:
        return _hk_result(raw_input, match.group(1), needs_confirmation=False)

    return None


def _normalize_a_share_digits(digits: str, raw_input: str, prefer_index: bool) -> NormalizedSymbol:
    if digits == "000001" and prefer_index:
        return NormalizedSymbol(
            raw_input=raw_input,
            normalized_symbol="000001.SH",
            market="CN",
            exchange="SH",
            asset_type="index",
            confidence=0.8,
            needs_confirmation=True,
            warnings=["000001 can mean an index or a stock; context preferred index."],
            source="context",
        )
    exchange = _infer_a_share_exchange(digits)
    if exchange is None:
        return NormalizedSymbol(
            raw_input=raw_input,
            normalized_symbol=None,
            market="CN",
            exchange=None,
            asset_type=None,
            confidence=0.0,
            needs_confirmation=True,
            warnings=[f"could not infer A-share exchange from prefix for {digits}"],
            source="invalid",
        )
    return _cn_result(raw_input, digits, exchange)


def _infer_a_share_exchange(digits: str) -> str | None:
    if digits.startswith(_SH_ETF_PREFIXES):
        return "SH"
    if digits.startswith(_SZ_ETF_PREFIXES):
        return "SZ"
    if digits.startswith(_SH_STOCK_PREFIXES):
        return "SH"
    if digits.startswith(_SZ_STOCK_PREFIXES):
        return "SZ"
    return None


def _asset_type_for_cn(digits: str, exchange: str) -> str:
    if exchange == "SH" and digits.startswith(_SH_ETF_PREFIXES):
        return "etf"
    if exchange == "SZ" and digits.startswith(_SZ_ETF_PREFIXES):
        return "etf"
    return "stock"


def _cn_result(raw_input: str, digits: str, exchange: str) -> NormalizedSymbol:
    normalized = f"{digits}.{exchange}"
    warnings: list[str] = []
    needs_confirmation = False
    if digits in _CN_AMBIGUOUS:
        warnings.append("000001 may refer to 000001.SZ stock or 000001.SH index depending on context.")
        needs_confirmation = True
    return NormalizedSymbol(
        raw_input=raw_input,
        normalized_symbol=normalized,
        market="CN",
        exchange=exchange,
        asset_type=_asset_type_for_cn(digits, exchange),
        confidence=0.9 if warnings else 0.95,
        needs_confirmation=needs_confirmation,
        warnings=warnings,
        source="rule",
    )


def _us_result(raw_input: str, ticker: str) -> NormalizedSymbol:
    return NormalizedSymbol(
        raw_input=raw_input,
        normalized_symbol=f"{ticker}.US",
        market="US",
        exchange="US",
        asset_type="etf" if ticker in _US_ETFS else "stock",
        confidence=0.95,
        needs_confirmation=False,
        source="rule",
    )


def _format_hk(digits: str) -> str:
    return f"{digits.zfill(5)}.HK"


def _hk_result(raw_input: str, digits: str, *, needs_confirmation: bool) -> NormalizedSymbol:
    return NormalizedSymbol(
        raw_input=raw_input,
        normalized_symbol=_format_hk(digits),
        market="HK",
        exchange="HK",
        asset_type="stock",
        confidence=0.9 if needs_confirmation else 0.95,
        needs_confirmation=needs_confirmation,
        warnings=["HK numeric code inferred without explicit context."] if needs_confirmation else [],
        source="rule",
    )
