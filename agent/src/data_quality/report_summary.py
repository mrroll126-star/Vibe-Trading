"""Report appendix helpers for data quality metadata."""

from __future__ import annotations

from typing import Any


QUALITY_STATUSES_REQUIRING_MISSING_NOTE = {"missing", "stale", "unknown"}


def append_data_source_summary(report: str, data_quality: dict[str, Any] | None) -> str:
    """Append a mechanical data-source appendix when quality metadata exists."""

    summary = format_data_source_summary(data_quality)
    if not summary:
        return report
    return f"{report.rstrip()}\n\n{summary}"


def format_data_source_summary(data_quality: dict[str, Any] | None) -> str:
    """Format `get_market_data` `_data_quality` metadata as markdown.

    The formatter is deliberately mechanical: it does not infer new facts or
    rewrite the model's analysis. It only exposes metadata that existing tools
    returned, so stale/missing/unknown data is visible in the final report.
    """

    if not isinstance(data_quality, dict) or not data_quality:
        return ""

    rows: list[tuple[str, dict[str, Any]]] = []
    for symbol, meta in data_quality.items():
        if symbol.startswith("_") or not isinstance(meta, dict):
            continue
        if meta.get("tool_name") != "get_market_data":
            continue
        rows.append((symbol, meta))

    if not rows:
        return ""

    lines = [
        "## Data Source Summary",
        "",
        "| tool_name | symbol | freshness_status | latest_data_date | latest_data_timestamp | requested_at | row_count | source_success | source_error |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for symbol, meta in rows:
        lines.append(
            "| {tool_name} | {symbol} | {freshness_status} | {latest_data_date} | {latest_data_timestamp} | {requested_at} | {row_count} | {source_success} | {source_error} |".format(
                tool_name=_cell(meta.get("tool_name")),
                symbol=_cell(meta.get("normalized_symbol") or symbol),
                freshness_status=_cell(meta.get("freshness_status")),
                latest_data_date=_cell(meta.get("latest_data_date")),
                latest_data_timestamp=_cell(meta.get("latest_data_timestamp")),
                requested_at=_cell(meta.get("requested_at")),
                row_count=_cell(meta.get("row_count")),
                source_success=_cell(meta.get("source_success")),
                source_error=_cell(meta.get("source_error")),
            )
        )

    missing_lines = _missing_data_lines(rows)
    if missing_lines:
        lines.extend(["", "## Missing Data", "", *missing_lines])

    warning_lines = _warning_lines(rows)
    if warning_lines:
        lines.extend(["", "## Source Warnings", "", *warning_lines])

    return "\n".join(lines)


def _missing_data_lines(rows: list[tuple[str, dict[str, Any]]]) -> list[str]:
    lines: list[str] = []
    for symbol, meta in rows:
        status = str(meta.get("freshness_status") or "").lower()
        if status not in QUALITY_STATUSES_REQUIRING_MISSING_NOTE:
            continue
        normalized = meta.get("normalized_symbol") or symbol
        if status == "missing":
            reason = "no usable market-data rows were returned"
        elif status == "stale":
            reason = "the latest market-data date is older than the request date"
        else:
            reason = "market data was returned without an extractable date or timestamp"
        lines.append(
            f"- {normalized}: `{status}` - {reason}; do not treat this as today's, intraday, latest, or realtime market fact."
        )
    return lines


def _warning_lines(rows: list[tuple[str, dict[str, Any]]]) -> list[str]:
    lines: list[str] = []
    for symbol, meta in rows:
        normalized = meta.get("normalized_symbol") or symbol
        warnings = meta.get("warnings") or []
        if not isinstance(warnings, list):
            continue
        for warning in warnings:
            if warning:
                lines.append(f"- {normalized}: {warning}")
    return lines


def _cell(value: Any) -> str:
    if value is None or value == "":
        return "n/a"
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text
