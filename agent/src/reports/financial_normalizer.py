"""Fixture-first normalization for primary financial statement envelopes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_PERIOD_FIELDS = ("report_date", "REPORT_DATE", "报告期", "date", "period")


def normalize_financial_statement_payload(
    payload: Mapping[str, Any] | None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one provider envelope into the report-builder tool-result shape.

    The function is deliberately mechanical: it copies only the provider's
    existing ``data[symbol].periods`` records, maps a known period field to
    ``report_date``, and emits warnings for missing provenance or periods.
    """

    source_payload = dict(payload or {})
    supplied_metadata = dict(metadata or {})
    statement_type = _text(source_payload.get("statement") or source_payload.get("statement_type"))
    source = _text(supplied_metadata.get("source") or source_payload.get("source"))
    provider = _text(supplied_metadata.get("provider") or source_payload.get("provider"))
    upstream = _text(supplied_metadata.get("upstream") or source_payload.get("upstream"))
    period = _text(source_payload.get("period"))
    warnings: list[str] = []

    if not statement_type:
        warnings.append("missing_statement_type")
    data = source_payload.get("data")
    symbol, periods = _extract_symbol_periods(data)
    if not symbol:
        warnings.append("missing_symbol_data")
    if not periods:
        warnings.append("missing_periods")
    if not provider:
        warnings.append("provider_missing")
    if not source:
        warnings.append("source_missing")

    rows = [_normalize_period_row(item) for item in periods]
    latest_period = _latest_period(rows)
    if rows and not latest_period:
        warnings.append("missing_reporting_period")

    quality = {
        "provider": provider,
        "source": source,
        "upstream": upstream,
        "latest_data_date": latest_period,
        "reporting_period": latest_period,
        "warnings": _dedupe(warnings),
    }
    return {
        "ok": bool(source_payload.get("ok", True)) and bool(statement_type and symbol and rows),
        "statement_type": statement_type,
        "period": period,
        "provider": provider,
        "source": source,
        "upstream": upstream,
        "data": {symbol: rows} if symbol else {},
        "_data_quality": {symbol: quality} if symbol else quality,
        "metadata": {
            "provider": provider,
            "source": source,
            "upstream": upstream,
            "report_periods": [value for value in (_period_from_row(row) for row in rows) if value],
        },
        "warnings": _dedupe(warnings),
    }


def _extract_symbol_periods(data: Any) -> tuple[str, list[dict[str, Any]]]:
    if not isinstance(data, Mapping):
        return "", []
    for raw_symbol, value in data.items():
        if not isinstance(value, Mapping):
            continue
        periods = value.get("periods")
        if isinstance(periods, list):
            return str(raw_symbol), [dict(item) for item in periods if isinstance(item, Mapping)]
    return "", []


def _normalize_period_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if "report_date" not in normalized:
        period = _period_from_row(normalized)
        if period:
            normalized["report_date"] = period
    return normalized


def _period_from_row(row: Mapping[str, Any]) -> str:
    for field in _PERIOD_FIELDS:
        value = row.get(field)
        if value is not None and str(value):
            return str(value)
    return ""


def _latest_period(rows: list[dict[str, Any]]) -> str:
    periods = [_period_from_row(row) for row in rows]
    return max((period for period in periods if period), default="")


def _text(value: Any) -> str:
    return str(value) if value is not None and str(value) else ""


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
