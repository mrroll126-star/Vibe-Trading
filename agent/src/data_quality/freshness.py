"""Freshness metadata helpers for market-data tool outputs.

The helper is intentionally network-free and provider-agnostic. It only
inspects the payload returned by existing loaders and emits additive metadata
that downstream prompts can use to avoid treating stale or ambiguous data as
today's facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any


DATE_KEYS = ("trade_date", "date", "datetime", "timestamp", "time")
DAILY_INTERVALS = {"1d", "1day", "day", "daily", "d"}


@dataclass
class FreshnessMetadata:
    tool_name: str
    raw_input: Any
    normalized_symbol: str | None
    market: str
    asset_type: str
    provider: str | None
    requested_at: str
    latest_data_date: str | None
    latest_data_timestamp: str | None
    freshness_status: str
    is_intraday_like: bool
    is_official_close: bool | None
    row_count: int
    source_success: bool
    source_error: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "raw_input": self.raw_input,
            "normalized_symbol": self.normalized_symbol,
            "market": self.market,
            "asset_type": self.asset_type,
            "provider": self.provider,
            "requested_at": self.requested_at,
            "latest_data_date": self.latest_data_date,
            "latest_data_timestamp": self.latest_data_timestamp,
            "freshness_status": self.freshness_status,
            "is_intraday_like": self.is_intraday_like,
            "is_official_close": self.is_official_close,
            "row_count": self.row_count,
            "source_success": self.source_success,
            "source_error": self.source_error,
            "warnings": list(self.warnings),
        }


def assess_freshness(
    data: Any,
    *,
    tool_name: str,
    raw_input: Any,
    normalized_symbol: str | None = None,
    provider: str | None = None,
    requested_at: datetime | None = None,
    interval: str = "1D",
    time_sensitive: bool = False,
    source_error: str | None = None,
) -> FreshnessMetadata:
    """Inspect a provider payload and return serializable freshness metadata."""

    requested_at = _ensure_datetime(requested_at)
    warnings: list[str] = []
    rows, explicit_error = _coerce_rows(data)
    source_error = source_error or explicit_error
    row_count = _reported_row_count(data, rows)
    source_success = not source_error and row_count > 0

    latest_dt = _latest_datetime(rows)
    latest_date = latest_dt.date() if latest_dt else None
    requested_date = requested_at.date()

    if source_error or row_count == 0:
        freshness_status = "missing"
        if not source_error:
            source_error = "No rows returned by data source."
        warnings.append("No usable market data was returned by the source.")
    elif latest_dt is None:
        freshness_status = "unknown"
        warnings.append("Market data was returned, but no date or timestamp could be extracted.")
    elif time_sensitive and latest_date < requested_date:
        freshness_status = "stale"
        warnings.append(
            f"Latest data date {latest_date.isoformat()} is older than requested date {requested_date.isoformat()}."
        )
    else:
        freshness_status = "fresh"

    is_intraday_like = False
    is_official_close: bool | None = None
    if latest_date == requested_date and _is_daily_interval(interval) and _has_close_field(rows):
        is_intraday_like = True
        is_official_close = False
        warnings.append(
            "Daily bar close on the current trading date may represent intraday last price, not official close."
        )

    market, asset_type = _classify_symbol(normalized_symbol or _raw_symbol(raw_input))

    return FreshnessMetadata(
        tool_name=tool_name,
        raw_input=raw_input,
        normalized_symbol=normalized_symbol,
        market=market,
        asset_type=asset_type,
        provider=provider,
        requested_at=requested_at.isoformat(),
        latest_data_date=latest_date.isoformat() if latest_date else None,
        latest_data_timestamp=latest_dt.isoformat() if latest_dt else None,
        freshness_status=freshness_status,
        is_intraday_like=is_intraday_like,
        is_official_close=is_official_close,
        row_count=row_count,
        source_success=source_success,
        source_error=source_error,
        warnings=warnings,
    )


def _ensure_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now().astimezone()
    if value.tzinfo is None:
        return value
    return value.astimezone()


def _coerce_rows(data: Any) -> tuple[list[dict[str, Any]], str | None]:
    if data is None:
        return [], None

    if hasattr(data, "reset_index") and hasattr(data, "to_dict"):
        return data.reset_index().to_dict(orient="records"), None

    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)], None

    if isinstance(data, dict):
        error = _extract_error(data)
        if data.get("ok") is False or error:
            return [], error or "Data source returned ok=false."
        if isinstance(data.get("data"), list):
            return [row for row in data["data"] if isinstance(row, dict)], None
        if isinstance(data.get("rows"), list):
            return [row for row in data["rows"] if isinstance(row, dict)], None
        if _looks_like_row(data):
            return [data], None

    return [], None


def _extract_error(data: dict[str, Any]) -> str | None:
    for key in ("error", "message", "source_error"):
        value = data.get(key)
        if value:
            return str(value)
    return None


def _reported_row_count(data: Any, rows: list[dict[str, Any]]) -> int:
    if isinstance(data, dict) and isinstance(data.get("rows"), int):
        return int(data["rows"])
    return len(rows)


def _looks_like_row(data: dict[str, Any]) -> bool:
    return any(key in data for key in DATE_KEYS) or any(key in data for key in ("open", "high", "low", "close"))


def _latest_datetime(rows: list[dict[str, Any]]) -> datetime | None:
    latest: datetime | None = None
    for row in rows:
        for key in DATE_KEYS:
            if key not in row:
                continue
            parsed = _parse_datetime(row[key])
            if parsed is not None and (latest is None or parsed > latest):
                latest = parsed
    return latest


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if hasattr(value, "to_pydatetime"):
        converted = value.to_pydatetime()
        return converted.replace(tzinfo=None) if converted.tzinfo else converted
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) == 8:
        try:
            return datetime.strptime(text, "%Y%m%d")
        except ValueError:
            return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        return None


def _is_daily_interval(interval: str) -> bool:
    return str(interval).strip().lower() in DAILY_INTERVALS


def _has_close_field(rows: list[dict[str, Any]]) -> bool:
    return any("close" in row for row in rows)


def _classify_symbol(symbol: str | None) -> tuple[str, str]:
    if not symbol:
        return "unknown", "unknown"
    upper = symbol.upper()
    if upper.startswith("LOCAL:"):
        return "local", "unknown"
    if upper.endswith((".SH", ".SZ", ".BJ")):
        if upper.startswith(("000", "399", "510", "159")):
            return "a_share", "index_or_etf"
        return "a_share", "equity"
    if upper.endswith(".US"):
        return "us_stock", "equity_or_etf"
    if upper.endswith(".HK"):
        return "hk_stock", "equity_or_etf"
    if upper.endswith("-USDT") or upper.endswith("/USDT"):
        return "crypto", "crypto"
    return "unknown", "unknown"


def _raw_symbol(raw_input: Any) -> str | None:
    if isinstance(raw_input, str):
        return raw_input
    if isinstance(raw_input, dict):
        value = raw_input.get("code") or raw_input.get("symbol") or raw_input.get("normalized_symbol")
        return str(value) if value else None
    return None
