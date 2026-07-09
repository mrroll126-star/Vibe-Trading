from __future__ import annotations

from collections.abc import Mapping
from typing import Any


DATE_KEYS = (
    "report_date",
    "reportDate",
    "date",
    "end_date",
    "endDate",
    "period",
    "报告期",
    "公告日期",
    "截止日期",
)

FIELD_ALIASES = {
    "revenue": ("revenue", "operating_revenue", "营业收入"),
    "net_profit": ("net_profit", "netProfit", "净利润", "归母净利润"),
    "total_assets": ("total_assets", "totalAssets", "总资产"),
    "total_liabilities": ("total_liabilities", "totalLiabilities", "总负债"),
    "cash_flow": ("cash_flow", "operating_cash_flow", "经营现金流", "经营活动现金流"),
    "eps": ("eps", "basic_eps", "每股收益", "基本每股收益"),
}


def normalize_a_stock_financials_result(
    raw: dict | list | None,
    symbol: str,
    source: str | None = None,
    upstream: str | None = None,
    statement_type: str | None = None,
) -> dict:
    """Normalize candidate a-stock-data financial rows into the local contract.

    This helper is deliberately pure: it does not import, execute, read from, or
    fetch from a-stock-data. It only reshapes already-provided payloads.
    """

    provider = "a_stock_data"
    source_name = _clean_text(source) or provider
    upstream_name = _clean_text(upstream) or "unknown"
    statement = _clean_text(statement_type)
    symbol_text = _clean_text(symbol) or ""
    warnings: list[str] = []
    errors: list[str] = []

    rows_payload = _extract_rows(raw, warnings=warnings, errors=errors)
    rows = [_normalize_row(row) for row in rows_payload if isinstance(row, Mapping)]

    if rows_payload and not rows:
        warnings.append("no_dict_rows")

    latest_date = _latest_date(
        str(row["report_date"]) for row in rows if row.get("report_date")
    )

    ok = bool(rows) and not errors
    freshness_status = "unknown" if ok else "missing"
    if ok and not latest_date:
        warnings.append("no_as_of_date")
    if not rows and not errors:
        errors.append("no financial rows returned")

    source_error = "; ".join(_dedupe(errors)) or None
    quality = {
        "tool_name": "get_financial_statements",
        "provider": provider,
        "source": source_name,
        "upstream": upstream_name,
        "statement_type": statement,
        "raw_input": symbol_text,
        "symbol": symbol_text,
        "normalized_symbol": symbol_text,
        "status": freshness_status,
        "freshness_status": freshness_status,
        "latest_date": latest_date,
        "latest_data_date": latest_date,
        "latest_data_timestamp": None,
        "requested_at": None,
        "row_count": len(rows),
        "source_success": ok,
        "source_error": source_error,
        "errors": _dedupe(errors),
        "warnings": _dedupe(warnings),
        "facts_available": ["financial_rows"] if rows else [],
        "facts_unavailable": [] if rows else ["financial_statements"],
    }

    return {
        "ok": ok,
        "symbol": symbol_text,
        "provider": provider,
        "source": source_name,
        "upstream": upstream_name,
        "statement_type": statement,
        "data": {symbol_text: rows},
        "_data_quality": {symbol_text: quality},
    }


def _extract_rows(
    raw: dict | list | None,
    *,
    warnings: list[str],
    errors: list[str],
) -> list[Any]:
    if raw is None:
        errors.append("empty raw financials payload")
        return []
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, Mapping):
        errors.append(f"unsupported raw financials payload type: {type(raw).__name__}")
        return []
    if not raw:
        return []

    ok_false = raw.get("ok") is False
    _collect_messages(raw, warnings=warnings, errors=errors, ok_false=ok_false)
    if ok_false:
        if not errors:
            errors.append("upstream returned ok=false")
        return []

    for key in ("data", "rows", "result", "periods", "items"):
        if key in raw:
            value = raw[key]
            if isinstance(value, list):
                return value
            if isinstance(value, Mapping):
                nested_rows = _extract_nested_rows(value)
                if nested_rows is not None:
                    return nested_rows
                return [value]
            if value is None:
                return []
            errors.append(f"unsupported {key} payload type: {type(value).__name__}")
            return []

    if _looks_like_financial_row(raw):
        return [raw]
    return []


def _extract_nested_rows(value: Mapping[str, Any]) -> list[Any] | None:
    for key in ("rows", "items", "data", "result", "periods"):
        nested = value.get(key)
        if isinstance(nested, list):
            return nested
    return None


def _collect_messages(
    raw: Mapping[str, Any],
    *,
    warnings: list[str],
    errors: list[str],
    ok_false: bool,
) -> None:
    for key in ("error", "errors"):
        _extend_texts(errors, raw.get(key))

    message = raw.get("message") or raw.get("msg")
    if ok_false:
        _extend_texts(errors, message)
    else:
        _extend_texts(warnings, message)

    for key in ("warning", "warnings"):
        _extend_texts(warnings, raw.get(key))


def _normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {"raw": dict(row)}
    report_date = _first_value(row, DATE_KEYS)
    if report_date is not None:
        normalized["report_date"] = _clean_text(report_date) or report_date

    for target, aliases in FIELD_ALIASES.items():
        value = _first_value(row, aliases)
        if value is not None:
            normalized[target] = value
    return normalized


def _looks_like_financial_row(raw: Mapping[str, Any]) -> bool:
    keys = set(raw)
    if keys.intersection(DATE_KEYS):
        return True
    for aliases in FIELD_ALIASES.values():
        if keys.intersection(aliases):
            return True
    return False


def _first_value(row: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _latest_date(values: Any) -> str | None:
    cleaned = [_clean_text(value) for value in values]
    cleaned = [value for value in cleaned if value]
    if not cleaned:
        return None
    return max(cleaned, key=_date_sort_key)


def _date_sort_key(value: str) -> str:
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return value


def _extend_texts(target: list[str], value: Any) -> None:
    if value is None or value == "":
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _extend_texts(target, item)
        return
    target.append(str(value))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

