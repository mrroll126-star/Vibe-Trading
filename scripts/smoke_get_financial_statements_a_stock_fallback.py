#!/usr/bin/env python3
"""Controlled direct smoke for a-stock-data financial fallback.

This script calls the real ``get_financial_statements`` tool path directly. It
does not enter AgentLoop, start Web UI, read ``agent/.env``, or change provider
chains. The primary Eastmoney/SEC path is forced to fail in-process so the
fallback path is deterministic and auditable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from src.tools.financial_statements_tool import FinancialStatementsTool  # noqa: E402


FORCED_PRIMARY_FAILURE = {
    "ok": False,
    "error": "forced_primary_failure_for_smoke",
    "data": [],
}


POSITIVE_CASES = (
    ("600519.SH", "income"),
    ("300750.SZ", "income"),
    ("600519.SH", "balance"),
    ("600519.SH", "cashflow"),
)

NEGATIVE_CASES = (
    ("510300.SH", "income", "etf_should_not_fallback"),
    ("QQQ.US", "income", "us_should_not_fallback"),
    ("000001.SH", "income", "index_should_not_fallback"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Direct smoke test for get_financial_statements a-stock-data fallback."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional ignored local directory for JSON output, e.g. local_reports.",
    )
    return parser.parse_args()


def _execute_tool(symbol: str, statement: str) -> dict[str, Any]:
    text = FinancialStatementsTool().execute(
        code=symbol,
        statement=statement,
        period="annual",
    )
    return json.loads(text)


def _quality_for(result: dict[str, Any], symbol: str) -> dict[str, Any]:
    quality = result.get("_data_quality")
    if isinstance(quality, dict):
        value = quality.get(symbol)
        if isinstance(value, dict):
            return value
    return {}


def run_positive_case(symbol: str, statement: str) -> dict[str, Any]:
    with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=FORCED_PRIMARY_FAILURE,
        ):
            result = _execute_tool(symbol, statement)

    rows = result.get("data", {}).get(symbol, []) if isinstance(result.get("data"), dict) else []
    quality = _quality_for(result, symbol)
    passed = (
        result.get("ok") is True
        and result.get("provider") == "a_stock_data"
        and result.get("source") == "sina_financial_report"
        and len(rows) > 0
        and bool(quality)
        and bool(quality.get("latest_data_date"))
        and "a_stock_data_fallback_used" in (quality.get("warnings") or [])
    )
    return {
        "case_type": "positive",
        "symbol": symbol,
        "statement": statement,
        "passed": passed,
        "ok": result.get("ok"),
        "provider": result.get("provider"),
        "source": result.get("source"),
        "upstream": result.get("upstream"),
        "row_count": len(rows),
        "latest_data_date": quality.get("latest_data_date"),
        "freshness_status": quality.get("freshness_status"),
        "primary_error": quality.get("primary_error"),
        "warnings": quality.get("warnings") or result.get("warnings") or [],
        "error": result.get("error"),
    }


def run_negative_case(symbol: str, statement: str, reason: str) -> dict[str, Any]:
    primary_patch = (
        "src.tools.financial_statements_tool._fetch_sec_statement"
        if symbol.endswith(".US")
        else "src.tools.financial_statements_tool._fetch_eastmoney_statement"
    )
    with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
        with patch(primary_patch, return_value=FORCED_PRIMARY_FAILURE):
            with patch("src.tools.financial_statements_tool.fetch_a_stock_financials") as fallback:
                result = _execute_tool(symbol, statement)

    warnings = result.get("warnings") or []
    fallback_meta = (result.get("fallback") or {}).get("a_stock_data") or {}
    passed = (
        fallback.call_count == 0
        and result.get("ok") is False
        and "a_stock_data_fallback_not_eligible" in warnings
        and fallback_meta.get("attempted") is False
    )
    return {
        "case_type": "negative",
        "symbol": symbol,
        "statement": statement,
        "reason": reason,
        "passed": passed,
        "ok": result.get("ok"),
        "fallback_called": fallback.call_count > 0,
        "fallback_attempted": fallback_meta.get("attempted"),
        "fallback_reason": fallback_meta.get("reason"),
        "warnings": warnings,
        "error": result.get("error"),
    }


def write_report(results: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"get_financial_statements_a_stock_fallback_smoke_{timestamp}.json"
    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": "scripts/smoke_get_financial_statements_a_stock_fallback.py",
        "forced_primary_failure": FORCED_PRIMARY_FAILURE,
        "results": results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    results: list[dict[str, Any]] = []

    for symbol, statement in POSITIVE_CASES:
        result = run_positive_case(symbol, statement)
        results.append(result)
        status = "OK" if result["passed"] else "FAILED"
        print(
            f"{status} positive {symbol} {statement}: "
            f"provider={result['provider']} source={result['source']} "
            f"rows={result['row_count']} latest={result['latest_data_date']} "
            f"error={result['error'] or ''}"
        )

    for symbol, statement, reason in NEGATIVE_CASES:
        result = run_negative_case(symbol, statement, reason)
        results.append(result)
        status = "OK" if result["passed"] else "FAILED"
        print(
            f"{status} negative {symbol} {statement}: "
            f"fallback_called={result['fallback_called']} "
            f"reason={result['fallback_reason']} error={result['error'] or ''}"
        )

    if args.output_dir:
        report_path = write_report(results, (ROOT / args.output_dir).resolve())
        print(f"JSON report: {report_path}")

    passed = sum(1 for item in results if item["passed"])
    print(f"Summary: {passed}/{len(results)} cases passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
