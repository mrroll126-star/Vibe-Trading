"""Minimal structured research report builder.

This module is intentionally pure and offline. It does not call providers,
AgentLoop, Web UI, or LLMs. It converts already-validated tool-like results
into the MVP Research Workspace schema proof.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.symbols import normalize_symbol


_INDEX_SYMBOLS = {
    "000001.SH",
    "000300.SH",
    "000905.SH",
    "399001.SZ",
    "399006.SZ",
}


class ReportBuildError(ValueError):
    """Raised when a structured report cannot be built safely."""


def build_research_report(
    *,
    input_symbol: str,
    market_result: dict[str, Any] | None = None,
    financial_results: list[dict[str, Any]] | None = None,
    interpretation: dict[str, Any] | None = None,
    run_id: str = "",
    generated_at: str | None = None,
    provider: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Build a minimal structured research report from tool-like results.

    Args:
        input_symbol: User or workflow symbol input. Must resolve safely.
        market_result: Mocked/validated market data tool result.
        financial_results: Mocked/validated financial statement tool results.
        interpretation: Optional LLM/Agent interpretation placeholders.
        run_id: Optional run identifier.
        generated_at: Optional ISO timestamp. Defaults to current UTC time.
        provider: Optional LLM provider metadata.
        model: Optional LLM model metadata.

    Returns:
        A JSON-serializable research report schema dictionary.

    Raises:
        ReportBuildError: If symbol resolution is invalid or needs confirmation.
    """

    symbol = _build_symbol_section(input_symbol)
    normalized_symbol = symbol["normalized_symbol"]
    financial_results = financial_results or []
    interpretation = interpretation or {}

    market_snapshot = _build_market_snapshot(normalized_symbol, market_result)
    financial_health = _build_financial_health(
        normalized_symbol,
        financial_results,
        asset_type=str(symbol.get("asset_type") or ""),
    )
    investment_memo = _build_investment_memo(interpretation)
    data_confidence = _build_data_confidence(
        market_snapshot=market_snapshot,
        financial_health=financial_health,
    )

    return {
        "research_meta": {
            "run_id": run_id,
            "generated_at": generated_at or datetime.now(UTC).isoformat(timespec="seconds"),
            "analysis_type": "single_stock_research",
            "provider": provider,
            "model": model,
            "data_sources": _collect_data_sources(data_confidence),
        },
        "symbol": symbol,
        "market_snapshot": market_snapshot,
        "financial_health": financial_health,
        "investment_memo": investment_memo,
        "valuation": _build_valuation_placeholder(),
        "risks": _build_risks(interpretation, data_confidence),
        "data_confidence": data_confidence,
        "limitations": _build_limitations(),
    }


def _build_symbol_section(input_symbol: str) -> dict[str, Any]:
    normalized = normalize_symbol(input_symbol)
    if not normalized.is_valid or normalized.needs_confirmation:
        raise ReportBuildError(
            "symbol must resolve to a single confirmed security before report schema generation"
        )
    asset_type = normalized.asset_type
    if normalized.normalized_symbol in _INDEX_SYMBOLS:
        asset_type = "index"

    return {
        "input": normalized.raw_input,
        "normalized_symbol": normalized.normalized_symbol,
        "display_name": normalized.name or "",
        "market": normalized.market,
        "asset_type": asset_type,
        "resolution_status": "resolved",
        "warnings": list(normalized.warnings),
    }


def _build_market_snapshot(symbol: str, result: dict[str, Any] | None) -> dict[str, Any]:
    quality = _quality_for(result, symbol)
    warnings = _warnings_from(result, quality)
    row = _latest_market_row(result, symbol)
    ok = bool(result and result.get("ok", True))
    has_row = bool(row)
    if result and has_row and not quality:
        warnings.append("market_data_quality_missing")

    if not result or not ok or not has_row:
        status = "missing"
    elif warnings:
        status = "partial"
    else:
        status = "available"

    return {
        "status": status,
        "price": _first_present(row, "price", "current_price", "latest_price", "close"),
        "change": _first_present(row, "change", "price_change"),
        "change_pct": _first_present(row, "change_pct", "pct_change", "percent_change"),
        "volume": _first_present(row, "volume", "vol"),
        "turnover": _first_present(row, "turnover", "amount"),
        "trend": {
            "summary": "",
            "period": str(row.get("period") or row.get("date") or row.get("timestamp") or ""),
            "facts": [],
        },
        "benchmark_comparison": {
            "benchmark_symbol": "",
            "benchmark_name": "",
            "relative_performance": None,
            "notes": "",
        },
        "data_quality": quality,
        "warnings": warnings,
    }


def _build_financial_health(
    symbol: str,
    results: list[dict[str, Any]],
    *,
    asset_type: str,
) -> dict[str, Any]:
    if asset_type and asset_type != "stock":
        return {
            "status": "blocked",
            "statements": [],
            "summary": {
                "revenue_trend": "",
                "profit_trend": "",
                "balance_sheet_view": "",
                "cashflow_view": "",
                "facts": [],
                "interpretation": "",
            },
            "quality": {
                "reporting_period_status": "not_applicable",
                "warnings": [f"company_financials_not_applicable_for_{asset_type}"],
            },
        }

    statements: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing_types: list[str] = []

    for result in results:
        statement_type = str(
            result.get("statement_type") or result.get("statement") or result.get("type") or "unknown"
        )
        quality = _quality_for(result, symbol)
        result_warnings = _warnings_from(result, quality)
        if result_warnings:
            warnings.extend(_dedupe(result_warnings))

        if not result.get("ok", False):
            missing_types.append(statement_type)
            error = result.get("error")
            if isinstance(error, str) and error:
                warnings.append(error)
            continue

        rows = _rows_for(result, symbol)
        if not rows:
            missing_types.append(statement_type)
            warnings.append(f"{statement_type}_statement_missing")
            continue
        if not quality:
            warnings.append(f"{statement_type}_data_quality_missing")

        statements.append(
            {
                "type": statement_type,
                "provider": str(result.get("provider") or quality.get("provider") or ""),
                "source": str(result.get("source") or quality.get("source") or ""),
                "upstream": str(result.get("upstream") or quality.get("upstream") or ""),
                "period": str(result.get("period") or ""),
                "latest_data_date": str(quality.get("latest_data_date") or _first_present(rows[0], "report_date", "报告期") or ""),
                "metrics": dict(rows[0]),
                "raw_rows_ref": "",
                "data_quality": quality,
            }
        )

    expected = {"income", "balance", "cashflow"}
    available = {item["type"] for item in statements}
    for statement_type in sorted(expected - available):
        if statement_type not in missing_types:
            missing_types.append(statement_type)

    if not statements:
        status = "missing"
    elif missing_types:
        status = "partial"
    else:
        status = "available"

    warnings.extend(f"{statement_type}_statement_missing" for statement_type in missing_types)
    return {
        "status": status,
        "statements": statements,
        "summary": {
            "revenue_trend": "",
            "profit_trend": "",
            "balance_sheet_view": "",
            "cashflow_view": "",
            "facts": [],
            "interpretation": "",
        },
        "quality": {
            "reporting_period_status": _financial_period_status(statements),
            "warnings": _dedupe(warnings),
        },
    }


def _build_investment_memo(interpretation: dict[str, Any]) -> dict[str, Any]:
    return {
        "thesis": str(interpretation.get("thesis") or ""),
        "bull_case": _string_list(interpretation.get("bull_case")),
        "bear_case": _string_list(interpretation.get("bear_case")),
        "key_risks": _string_list(interpretation.get("key_risks")),
        "monitor_items": _string_list(interpretation.get("monitor_items")),
    }


def _build_data_confidence(
    *,
    market_snapshot: dict[str, Any],
    financial_health: dict[str, Any],
) -> dict[str, Any]:
    market_quality = market_snapshot.get("data_quality") if isinstance(market_snapshot.get("data_quality"), dict) else {}
    financial_statements = financial_health.get("statements") if isinstance(financial_health.get("statements"), list) else []
    first_financial = financial_statements[0] if financial_statements else {}
    financial_quality = first_financial.get("data_quality") if isinstance(first_financial.get("data_quality"), dict) else {}
    warnings = _dedupe(
        _string_list(market_snapshot.get("warnings"))
        + _string_list(financial_health.get("quality", {}).get("warnings") if isinstance(financial_health.get("quality"), dict) else [])
    )

    return {
        "market_data": {
            "provider": str(market_quality.get("provider") or ""),
            "source": str(market_quality.get("source") or ""),
            "date": str(market_quality.get("latest_data_date") or ""),
            "status": market_snapshot.get("status") or "unknown",
            "warnings": _string_list(market_quality.get("warnings")),
        },
        "financial_data": {
            "provider": str(first_financial.get("provider") or financial_quality.get("provider") or ""),
            "source": str(first_financial.get("source") or financial_quality.get("source") or ""),
            "upstream": str(first_financial.get("upstream") or financial_quality.get("upstream") or ""),
            "reporting_period": str(financial_quality.get("reporting_period") or ""),
            "period_end_date": str(first_financial.get("latest_data_date") or financial_quality.get("latest_data_date") or ""),
            "status": financial_health.get("status") or "unknown",
            "warnings": _string_list(financial_health.get("quality", {}).get("warnings") if isinstance(financial_health.get("quality"), dict) else []),
        },
        "warnings": warnings,
    }


def _build_valuation_placeholder() -> dict[str, Any]:
    return {
        "status": "partial",
        "available_metrics": [],
        "missing_metrics": ["PE", "PB", "target_price"],
        "missing_inputs": ["market_cap", "shares_outstanding", "forecast_earnings"],
        "reason": "Valuation requires financial data, market data, shares or market cap, and period alignment.",
    }


def _build_risks(interpretation: dict[str, Any], data_confidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "business_risks": _string_list(interpretation.get("business_risks")),
        "financial_risks": _string_list(interpretation.get("financial_risks")),
        "market_risks": _string_list(interpretation.get("market_risks")),
        "data_risks": _string_list(data_confidence.get("warnings")),
        "unsupported_risks": [],
    }


def _build_limitations() -> dict[str, Any]:
    return {
        "unsupported": [
            "analyst_forecast",
            "target_price",
            "peer_comparison",
            "earnings_call",
            "automatic_buy_sell_decision",
        ],
        "notes": [
            "Financial indicators are treated as future derived metrics, not an independent MVP data source.",
            "Markdown should be generated from schema, not treated as the source of truth.",
        ],
    }


def _collect_data_sources(data_confidence: dict[str, Any]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for key in ("market_data", "financial_data", "news_data"):
        item = data_confidence.get(key)
        if not isinstance(item, dict):
            continue
        provider = str(item.get("provider") or "")
        source = str(item.get("source") or "")
        if provider or source:
            sources.append({"section": key, "provider": provider, "source": source})
    return sources


def _quality_for(result: dict[str, Any] | None, symbol: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    quality = result.get("_data_quality")
    if isinstance(quality, dict):
        value = quality.get(symbol)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _warnings_from(result: dict[str, Any] | None, quality: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if isinstance(result, dict):
        warnings.extend(_string_list(result.get("warnings")))
        error = result.get("error")
        if isinstance(error, str) and error:
            warnings.append(error)
    warnings.extend(_string_list(quality.get("warnings")))
    return _dedupe(warnings)


def _latest_market_row(result: dict[str, Any] | None, symbol: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    data = result.get("data")
    if isinstance(data, dict):
        rows = data.get(symbol)
        if isinstance(rows, list) and rows:
            latest = rows[-1]
            return dict(latest) if isinstance(latest, dict) else {}
        if isinstance(rows, dict):
            return dict(rows)
    rows = result.get(symbol)
    if isinstance(rows, list) and rows:
        latest = rows[-1]
        return dict(latest) if isinstance(latest, dict) else {}
    return {}


def _rows_for(result: dict[str, Any], symbol: str) -> list[dict[str, Any]]:
    data = result.get("data")
    if isinstance(data, dict):
        rows = data.get(symbol)
        if isinstance(rows, list):
            return [dict(row) for row in rows if isinstance(row, dict)]
        if isinstance(rows, dict):
            periods = rows.get("periods")
            if isinstance(periods, list):
                return [dict(row) for row in periods if isinstance(row, dict)]
    if isinstance(data, list):
        return [dict(row) for row in data if isinstance(row, dict)]
    return []


def _financial_period_status(statements: list[dict[str, Any]]) -> str:
    if not statements:
        return "missing"
    if any(not statement.get("latest_data_date") for statement in statements):
        return "unknown"
    return "available"


def _first_present(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in source and source[key] not in (None, ""):
            return source[key]
    return None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
