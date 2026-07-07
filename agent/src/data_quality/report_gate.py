"""Time-sensitive report gate for market-data freshness metadata."""

from __future__ import annotations

from typing import Any

from .report_summary import format_data_source_summary

TIME_SENSITIVE_TERMS = [
    "今天",
    "今日",
    "盘中",
    "实时",
    "最新",
    "当前",
    "刚刚",
    "收盘",
    "当日",
    "涨跌幅",
    "成交额",
    "成交量",
    "资金流",
    "today",
    "intraday",
    "real-time",
    "realtime",
    "latest",
    "current",
    "close",
    "closing price",
    "volume",
    "turnover",
    "price change",
]

CLOSE_TERMS = ["收盘", "收盘价", "closing price", "official close", "close"]
BLOCKING_STATUSES = {"stale", "missing", "unknown"}


def detect_time_sensitive_request(prompt: str) -> dict[str, Any]:
    """Detect whether a prompt asks for time-sensitive market facts."""

    text = (prompt or "").lower()
    matched_terms = []
    for term in TIME_SENSITIVE_TERMS:
        if term.lower() in text:
            matched_terms.append(term)

    return {
        "is_time_sensitive": bool(matched_terms),
        "matched_terms": matched_terms,
        "reason": "matched time-sensitive market terms" if matched_terms else "no time-sensitive market terms matched",
    }


def evaluate_market_data_report_gate(prompt: str, data_quality: dict[str, Any] | None) -> dict[str, Any]:
    """Evaluate whether a final report should be blocked for freshness risk."""

    sensitivity = detect_time_sensitive_request(prompt)
    result: dict[str, Any] = {
        "blocked": False,
        "reason": "",
        "symbols": [],
        "blocking_statuses": [],
        "matched_terms": sensitivity["matched_terms"],
        "details": [],
        "warnings": [],
    }

    if not sensitivity["is_time_sensitive"]:
        result["reason"] = "Prompt is not time-sensitive."
        return result

    rows = _quality_rows(data_quality)
    if not rows:
        result["reason"] = "Prompt is time-sensitive, but no get_market_data _data_quality was available; MVP does not block this case."
        result["warnings"].append("No get_market_data _data_quality available for gate evaluation.")
        return result

    asks_for_close = _asks_for_official_close(prompt)
    for symbol, meta in rows:
        status = str(meta.get("freshness_status") or "").lower()
        warnings = _warnings(meta)
        normalized = str(meta.get("normalized_symbol") or symbol)

        if status in BLOCKING_STATUSES:
            _add_blocking_detail(result, normalized, status, meta, "freshness_status blocks time-sensitive report")
            continue

        if status == "fresh" and asks_for_close and _has_official_close_warning(warnings):
            _add_blocking_detail(
                result,
                normalized,
                "fresh_with_unofficial_close_warning",
                meta,
                "prompt asks for closing price, but daily close warning says it may not be official close",
            )
        elif warnings:
            result["warnings"].append(f"{normalized}: " + "; ".join(warnings))

    if result["details"]:
        result["blocked"] = True
        result["symbols"] = [detail["symbol"] for detail in result["details"]]
        result["blocking_statuses"] = sorted({detail["freshness_status"] for detail in result["details"]})
        result["reason"] = "Time-sensitive request has stale, missing, unknown, or unofficial-close market data."
    else:
        result["reason"] = "Time-sensitive request has no blocking get_market_data freshness status."

    return result


def format_data_insufficient_report(gate_result: dict[str, Any], data_quality: dict[str, Any] | None) -> str:
    """Return a deterministic report when time-sensitive market data is unsafe."""

    matched = ", ".join(gate_result.get("matched_terms") or []) or "n/a"
    symbols = ", ".join(gate_result.get("symbols") or []) or "n/a"
    lines = [
        "# Data Insufficient Report",
        "",
        "## Why this report is blocked",
        "",
        f"- The user request is time-sensitive. Matched terms: {matched}.",
        "- Current `get_market_data` freshness metadata does not satisfy the requirement for today's, intraday, latest, realtime, or official-close factual analysis.",
        "- A normal factual market report is blocked to avoid inventing prices, percent changes, volume, turnover, or other market facts.",
        f"- Affected symbol(s): {symbols}.",
        "",
    ]

    source_summary = format_data_source_summary(data_quality)
    if source_summary:
        lines.extend([source_summary, ""])

    missing = _format_missing_or_unreliable(gate_result)
    if missing:
        lines.extend(["## Missing or Unreliable Data", "", *missing, ""])

    lines.extend(
        [
            "## What can be done instead",
            "",
            "- Ask for a historical overview based only on the latest available dated data.",
            "- Retry after the data source returns current trading-day data.",
            "- Provide a trusted data file, table, or screenshot for the system to cite explicitly.",
            "- This report is not investment advice.",
        ]
    )
    return "\n".join(lines).rstrip()


def _quality_rows(data_quality: dict[str, Any] | None) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(data_quality, dict):
        return []
    rows: list[tuple[str, dict[str, Any]]] = []
    for symbol, meta in data_quality.items():
        if not isinstance(symbol, str) or symbol.startswith("_") or not isinstance(meta, dict):
            continue
        if meta.get("tool_name") != "get_market_data":
            continue
        rows.append((symbol, meta))
    return rows


def _asks_for_official_close(prompt: str) -> bool:
    text = (prompt or "").lower()
    return any(term.lower() in text for term in CLOSE_TERMS)


def _warnings(meta: dict[str, Any]) -> list[str]:
    warnings = meta.get("warnings") or []
    if not isinstance(warnings, list):
        return []
    return [str(warning) for warning in warnings if warning]


def _has_official_close_warning(warnings: list[str]) -> bool:
    return any("not official close" in warning.lower() or "不是正式收盘" in warning for warning in warnings)


def _add_blocking_detail(
    result: dict[str, Any],
    symbol: str,
    status: str,
    meta: dict[str, Any],
    reason: str,
) -> None:
    result["details"].append(
        {
            "symbol": symbol,
            "freshness_status": status,
            "latest_data_date": meta.get("latest_data_date"),
            "latest_data_timestamp": meta.get("latest_data_timestamp"),
            "requested_at": meta.get("requested_at"),
            "source_error": meta.get("source_error"),
            "warnings": _warnings(meta),
            "reason": reason,
        }
    )


def _format_missing_or_unreliable(gate_result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for detail in gate_result.get("details") or []:
        warnings = detail.get("warnings") or []
        warning_text = "; ".join(warnings) if warnings else "n/a"
        lines.append(
            "- {symbol}: freshness_status={status}, latest_data_date={date}, requested_at={requested_at}, source_error={error}, warnings={warnings}".format(
                symbol=detail.get("symbol") or "n/a",
                status=detail.get("freshness_status") or "n/a",
                date=detail.get("latest_data_date") or "n/a",
                requested_at=detail.get("requested_at") or "n/a",
                error=detail.get("source_error") or "n/a",
                warnings=warning_text,
            )
        )
    return lines
