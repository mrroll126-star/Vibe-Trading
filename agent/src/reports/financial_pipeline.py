"""Report-consumer normalization for collected financial tool results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.reports.financial_normalizer import normalize_financial_statement_payload


def normalize_financial_results_for_report(
    financial_results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return canonical statement results plus non-blocking normalization warnings.

    Each provider result remains an independent record. The function never
    merges rows or provenance across providers and leaves legacy canonical rows
    unchanged.
    """

    normalized_results: list[dict[str, Any]] = []
    warnings: list[str] = []
    for result in financial_results:
        if not _is_periods_envelope(result):
            normalized_results.append(dict(result))
            continue
        statement_type = str(result.get("statement") or result.get("statement_type") or "unknown")
        try:
            normalized = normalize_financial_statement_payload(
                result,
                metadata=_trace_metadata(result),
            )
        except Exception:  # noqa: BLE001 - normalization must not block report assembly
            normalized_results.append(dict(result))
            warnings.append(f"financial_normalizer_failed:{statement_type}")
            continue
        normalized_results.append(normalized)
        warnings.extend(
            f"financial_normalizer:{statement_type}:{warning}"
            for warning in normalized.get("warnings", [])
            if isinstance(warning, str) and warning
        )
    return normalized_results, _dedupe(warnings)


def _is_periods_envelope(result: Mapping[str, Any]) -> bool:
    data = result.get("data")
    if not isinstance(data, Mapping):
        return False
    return any(isinstance(value, Mapping) for value in data.values()) and not any(
        isinstance(value, list) for value in data.values()
    )


def _trace_metadata(result: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = result.get("_trace_metadata")
    return metadata if isinstance(metadata, Mapping) else {}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
