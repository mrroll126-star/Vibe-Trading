"""Pure fixture-first financial confidence extraction for report schema proofs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CORE_STATEMENTS = ("income", "balance", "cashflow")


class FinancialConfidenceError(ValueError):
    """Raised when financial confidence is requested for an unsupported asset."""


def extract_financial_confidence(
    financial_results: Mapping[str, Mapping[str, Any]] | None,
    *,
    asset_type: str = "stock",
) -> dict[str, Any]:
    """Build financial confidence from already-loaded tool-result fixtures.

    This function is intentionally pure: it does not call providers, AgentLoop,
    Web UI, or an LLM. `financial_results` is expected to map statement types
    to tool-like dictionaries.
    """

    if asset_type != "stock":
        raise FinancialConfidenceError(
            f"financial confidence is not applicable for asset_type={asset_type!r}"
        )

    results = financial_results or {}
    statement_confidence = [
        _statement_confidence(statement_type, _mapping_or_empty(results.get(statement_type)))
        for statement_type in CORE_STATEMENTS
    ]
    warnings = _dedupe(
        warning
        for statement in statement_confidence
        for warning in statement["warnings"]
    )
    status = _combined_status(statement_confidence)
    periods = [
        str(statement["latest_period"])
        for statement in statement_confidence
        if statement["latest_period"]
    ]
    providers = _dedupe(
        str(statement["provider"])
        for statement in statement_confidence
        if statement["provider"]
    )
    sources = _dedupe(
        str(statement["source"])
        for statement in statement_confidence
        if statement["source"]
    )
    upstreams = _dedupe(
        str(statement["upstream"])
        for statement in statement_confidence
        if statement["upstream"]
    )
    fallback_used = any(bool(statement["fallback_used"]) for statement in statement_confidence)
    reporting_period_status = _combined_period_status(statement_confidence)

    financial_health = {
        "status": status,
        "statement_level_confidence": statement_confidence,
        "reporting_period": {
            "latest_period": max(periods) if periods else "",
            "status": reporting_period_status,
        },
        "freshness_policy": {
            "policy": "reporting_period",
            "market_freshness_reused": False,
        },
        "fallback_status": {
            "fallback_used": fallback_used,
            "statement_types": [
                statement["statement_type"]
                for statement in statement_confidence
                if statement["fallback_used"]
            ],
        },
        "warnings": warnings,
    }
    financial_data = {
        "status": status,
        "statements": {
            statement["statement_type"]: statement for statement in statement_confidence
        },
        "providers": providers,
        "sources": sources,
        "upstreams": upstreams,
        "reporting_period": max(periods) if periods else "",
        "reporting_period_status": reporting_period_status,
        "fallback_used": fallback_used,
        "warnings": warnings,
    }
    return {
        "financial_health": financial_health,
        "data_confidence": {"financial_data": financial_data},
        "warnings": warnings,
    }


def _statement_confidence(statement_type: str, result: Mapping[str, Any]) -> dict[str, Any]:
    quality = _quality_metadata(result)
    rows = _rows(result)
    provider = _first_text(result.get("provider"), quality.get("provider"))
    source = _first_text(result.get("source"), quality.get("source"))
    upstream = _first_text(result.get("upstream"), quality.get("upstream"))
    latest_period = _first_text(
        result.get("latest_data_date"),
        quality.get("latest_data_date"),
        quality.get("reporting_period"),
        _row_period(rows),
    )
    ok = bool(result.get("ok", False))
    fallback_used = bool(
        result.get("fallback")
        or result.get("fallback_used")
        or quality.get("fallback")
        or quality.get("fallback_used")
    )
    warnings = _string_list(result.get("warnings")) + _string_list(quality.get("warnings"))

    if not result:
        status = "missing"
        warnings.append(f"{statement_type}_statement_missing")
    elif not ok:
        status = "failed"
        warnings.append(f"{statement_type}_statement_failed")
        error = result.get("error")
        if isinstance(error, str) and error:
            warnings.append(error)
    elif not rows:
        status = "missing"
        warnings.append(f"{statement_type}_statement_missing")
    else:
        status = "available"

    if status == "available" and not provider:
        warnings.append("provider_missing")
        status = "partial"
    if status in {"available", "partial"} and not source:
        warnings.append("source_missing")
        status = "partial"
    if status in {"available", "partial"} and not latest_period:
        warnings.append("missing_reporting_period")
        status = "partial"
    if fallback_used:
        warnings.append("fallback_provider_used")

    completeness = "sufficient" if status == "available" else ("partial" if status == "partial" else "insufficient")
    quality_status = "reported_period_available" if latest_period else "reporting_period_unknown"
    period_status = "period_available_but_age_unassessed" if latest_period else "missing_period"

    return {
        "statement_type": statement_type,
        "status": status,
        "provider": provider,
        "source": source,
        "upstream": upstream,
        "latest_period": latest_period,
        "row_count": len(rows),
        "completeness": completeness,
        "quality_status": quality_status,
        "reporting_period_status": period_status,
        "fallback_used": fallback_used,
        "primary_error": _first_text(result.get("primary_error"), quality.get("primary_error")),
        "warnings": _dedupe(warnings),
    }


def _combined_status(statements: list[dict[str, Any]]) -> str:
    statuses = {str(statement["status"]) for statement in statements}
    if statuses == {"available"}:
        return "complete"
    if statuses <= {"missing", "failed"}:
        return "missing"
    return "partial"


def _combined_period_status(statements: list[dict[str, Any]]) -> str:
    statuses = {str(statement["reporting_period_status"]) for statement in statements}
    if "missing_period" in statuses:
        return "missing_period"
    if "stale_for_expected_cycle" in statuses:
        return "stale_for_expected_cycle"
    if statuses == {"period_available_but_age_unassessed"}:
        return "period_available_but_age_unassessed"
    return "unknown"


def _quality_metadata(result: Mapping[str, Any]) -> dict[str, Any]:
    quality = result.get("_data_quality")
    if not isinstance(quality, Mapping):
        return {}
    if any(key in quality for key in ("provider", "source", "latest_data_date", "warnings")):
        return dict(quality)
    for value in quality.values():
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    data = result.get("data")
    if isinstance(data, list):
        return [dict(row) for row in data if isinstance(row, Mapping)]
    if isinstance(data, Mapping):
        for value in data.values():
            if isinstance(value, list):
                return [dict(row) for row in value if isinstance(row, Mapping)]
    return []


def _row_period(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    return _first_text(rows[0].get("report_date"), rows[0].get("报告期"), rows[0].get("date"))


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_text(*values: Any) -> str:
    for value in values:
        if value is not None and str(value):
            return str(value)
    return ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
