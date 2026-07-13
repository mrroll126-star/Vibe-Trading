"""Mechanical financial provenance projection for structured trace proofs.

The helpers in this module are pure. They consume only an already-structured
financial result and explicit runtime/serializer metadata; they never parse
legacy result text, call providers, or infer facts from dates or tool names.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_PERIOD_FIELDS = ("report_date", "REPORT_DATE", "报告期", "date", "period")
_CORE_STATEMENTS = {"income", "balance", "cashflow"}


def project_financial_provenance(
    *,
    payload: Mapping[str, Any] | None,
    tool_name: str,
    tool_args: Mapping[str, Any] | None,
    execution_metadata: Mapping[str, Any] | None,
    serializer_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project verified primary/fallback facts into a provenance envelope.

    Field precedence is structured payload, explicit execution metadata, then
    serializer metadata. Only statement period and row count may be derived,
    and only from existing structured rows.
    """

    source_payload = dict(payload or {})
    args = dict(tool_args or {})
    execution = dict(execution_metadata or {})
    serializer = dict(serializer_metadata or {})
    symbol, rows = _structured_rows(source_payload)
    statement_type = _first_text(
        source_payload.get("statement_type"),
        source_payload.get("statement"),
        execution.get("statement_type"),
        args.get("statement_type"),
        args.get("statement"),
        serializer.get("statement_type"),
    )
    provider = _first_text(
        source_payload.get("provider"),
        execution.get("provider"),
        serializer.get("provider"),
    )
    source = _first_text(
        source_payload.get("source"),
        execution.get("source"),
        serializer.get("source"),
    )
    upstream = _first_text(
        source_payload.get("upstream"),
        execution.get("upstream"),
        serializer.get("upstream"),
    )
    periods = _periods(rows)
    latest_period = max(periods) if periods else ""
    fallback_used, fallback_known = _fallback_status(source_payload, execution, serializer)
    primary_error = _first_text(
        source_payload.get("primary_error"),
        _fallback_primary_error(source_payload),
        execution.get("primary_error"),
        _fallback_primary_error(execution),
        serializer.get("primary_error"),
        _fallback_primary_error(serializer),
    )

    warnings = _input_warnings(source_payload, execution, serializer)
    if tool_name != "get_financial_statements":
        warnings.append("financial_provenance_unsupported_tool")
    if statement_type and statement_type not in _CORE_STATEMENTS:
        warnings.append("unsupported_financial_statement_type")
    if not statement_type:
        warnings.append("missing_statement_type")
    if not provider:
        warnings.append("financial_provider_missing")
    if not source:
        warnings.append("financial_source_missing")
    if not upstream:
        warnings.append("financial_upstream_missing")
    if not periods:
        warnings.append("missing_reporting_period")
    if not rows:
        warnings.append("financial_rows_missing")
    if not fallback_known:
        warnings.append("fallback_status_unknown")
    if fallback_used:
        warnings.append("fallback_provider_used")

    warnings = _dedupe(warnings)
    quality_status = "available" if _quality_complete(
        tool_name=tool_name,
        statement_type=statement_type,
        provider=provider,
        source=source,
        latest_period=latest_period,
        row_count=len(rows),
    ) else "partial"
    data_quality = {
        "provider": provider,
        "source": source,
        "upstream": upstream,
        "latest_data_date": latest_period,
        "reporting_period": latest_period,
        "row_count": len(rows),
        "quality_status": quality_status,
        "warnings": warnings,
    }
    return {
        "provider": provider,
        "source": source,
        "upstream": upstream,
        "statement_type": statement_type,
        "symbol": symbol,
        "reporting_period": {"latest": latest_period, "periods": periods},
        "row_count": len(rows),
        "data_quality": data_quality,
        "fallback_status": {
            "used": fallback_used if fallback_known else None,
            "primary_error": primary_error or None,
        },
        "warnings": warnings,
    }


def build_financial_provenance_enrichment(
    *,
    payload: Mapping[str, Any] | None,
    tool_name: str,
    tool_args: Mapping[str, Any] | None,
    execution_metadata: Mapping[str, Any] | None,
    serializer_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a future runtime dual-write enrichment without mutating payload.

    This fixture-only adapter demonstrates the producer/projector boundary. A
    future runtime hook may attach the returned ``structured_payload`` and
    ``metadata`` to a trace event while preserving legacy text unchanged.
    """

    projection = project_financial_provenance(
        payload=payload,
        tool_name=tool_name,
        tool_args=tool_args,
        execution_metadata=execution_metadata,
        serializer_metadata=serializer_metadata,
    )
    enriched_payload = dict(payload or {})
    for field in ("provider", "source", "upstream", "statement_type"):
        if projection[field]:
            enriched_payload[field] = projection[field]
    enriched_payload["fallback_used"] = projection["fallback_status"]["used"]
    if projection["fallback_status"]["primary_error"]:
        enriched_payload["primary_error"] = projection["fallback_status"]["primary_error"]
    if projection["symbol"]:
        enriched_payload["_data_quality"] = {
            projection["symbol"]: dict(projection["data_quality"])
        }
    enriched_payload["warnings"] = list(projection["warnings"])

    metadata = {
        "provider": projection["provider"],
        "source": projection["source"],
        "upstream": projection["upstream"],
        "statement_type": projection["statement_type"],
        "reporting_period": projection["reporting_period"],
        "row_count": projection["row_count"],
        "data_quality": (
            {projection["symbol"]: dict(projection["data_quality"])}
            if projection["symbol"]
            else dict(projection["data_quality"])
        ),
        "fallback_status": dict(projection["fallback_status"]),
        "warnings": list(projection["warnings"]),
    }
    return {
        "structured_payload": enriched_payload,
        "metadata": metadata,
        "warnings": list(projection["warnings"]),
        "projection": projection,
    }


def _structured_rows(payload: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        return "", []
    for raw_symbol, value in data.items():
        if isinstance(value, Mapping) and isinstance(value.get("periods"), list):
            return str(raw_symbol), [dict(row) for row in value["periods"] if isinstance(row, Mapping)]
        if isinstance(value, list):
            return str(raw_symbol), [dict(row) for row in value if isinstance(row, Mapping)]
    return "", []


def _periods(rows: list[dict[str, Any]]) -> list[str]:
    periods: list[str] = []
    for row in rows:
        period = _first_text(*(row.get(field) for field in _PERIOD_FIELDS))
        if period:
            periods.append(period)
    return _dedupe(periods)


def _fallback_status(
    payload: Mapping[str, Any], execution: Mapping[str, Any], serializer: Mapping[str, Any]
) -> tuple[bool, bool]:
    for source in (payload, execution, serializer):
        for field in ("fallback_used", "fallback"):
            if field in source and source[field] is not None:
                if isinstance(source[field], Mapping):
                    if source[field].get("used") is not None:
                        return bool(source[field]["used"]), True
                    return True, True
                return bool(source[field]), True
    status = execution.get("fallback_status")
    if isinstance(status, Mapping) and status.get("used") is not None:
        return bool(status["used"]), True
    return False, False


def _fallback_primary_error(source: Mapping[str, Any]) -> Any:
    fallback = source.get("fallback")
    if not isinstance(fallback, Mapping):
        return None
    primary = fallback.get("primary")
    return primary.get("error") if isinstance(primary, Mapping) else None


def _input_warnings(*sources: Mapping[str, Any]) -> list[str]:
    warnings: list[str] = []
    for source in sources:
        value = source.get("warnings")
        if isinstance(value, list):
            warnings.extend(str(item) for item in value if str(item))
        quality = source.get("_data_quality") or source.get("data_quality")
        if isinstance(quality, Mapping):
            warnings.extend(_quality_warnings(quality))
    return warnings


def _quality_warnings(quality: Mapping[str, Any]) -> list[str]:
    direct = quality.get("warnings")
    if isinstance(direct, list):
        return [str(item) for item in direct if str(item)]
    for value in quality.values():
        if isinstance(value, Mapping):
            nested = value.get("warnings")
            if isinstance(nested, list):
                return [str(item) for item in nested if str(item)]
    return []


def _quality_complete(
    *,
    tool_name: str,
    statement_type: str,
    provider: str,
    source: str,
    latest_period: str,
    row_count: int,
) -> bool:
    return (
        tool_name == "get_financial_statements"
        and statement_type in _CORE_STATEMENTS
        and bool(provider)
        and bool(source)
        and bool(latest_period)
        and row_count > 0
    )


def _first_text(*values: Any) -> str:
    for value in values:
        if value is not None and str(value):
            return str(value)
    return ""


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
