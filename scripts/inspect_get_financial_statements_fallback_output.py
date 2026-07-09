#!/usr/bin/env python3
"""Inspect direct financial fallback output shape.

This script is intentionally narrow. It calls ``FinancialStatementsTool``
directly with the a-stock-data fallback flag enabled only inside this process,
forces the primary provider to fail, and prints a compact structure summary.
It does not enter AgentLoop, start Web UI, or read ``agent/.env``.
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

from src.adapters.a_stock_data.financials import fetch_a_stock_financials as live_fetch  # noqa: E402
from src.tools.financial_statements_tool import FinancialStatementsTool  # noqa: E402


FORCED_PRIMARY_FAILURE = {
    "ok": False,
    "error": "forced_primary_failure_for_output_inspection",
    "data": [],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a-stock-data financial fallback output shape."
    )
    parser.add_argument(
        "--symbols",
        default="600519.SH",
        help="Comma-separated explicit symbols. Default keeps this to one live request.",
    )
    parser.add_argument(
        "--statement-types",
        default="income",
        help="Comma-separated statement types: income,balance,cashflow.",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="Live fallback timeout seconds.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional ignored local directory for compact JSON summaries, e.g. local_reports.",
    )
    return parser.parse_args()


def _execute_tool(symbol: str, statement_type: str, *, timeout: float) -> dict[str, Any]:
    def _fetch_with_timeout(symbol_arg: str, statement_type: str | None = None, **kwargs: Any) -> dict[str, Any]:
        kwargs["timeout"] = timeout
        return live_fetch(symbol_arg, statement_type=statement_type, **kwargs)

    with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=FORCED_PRIMARY_FAILURE,
        ):
            with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", side_effect=_fetch_with_timeout):
                text = FinancialStatementsTool().execute(
                    code=symbol,
                    statement=statement_type,
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


def _rows_for(result: dict[str, Any], symbol: str) -> list[Any]:
    data = result.get("data")
    if isinstance(data, dict):
        rows = data.get(symbol)
        if isinstance(rows, list):
            return rows
    return []


def inspect_one(symbol: str, statement_type: str, *, timeout: float) -> dict[str, Any]:
    result = _execute_tool(symbol, statement_type, timeout=timeout)
    rows = _rows_for(result, symbol)
    quality = _quality_for(result, symbol)
    first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
    warnings = quality.get("warnings") if isinstance(quality.get("warnings"), list) else []
    errors = quality.get("errors") if isinstance(quality.get("errors"), list) else []
    summary = {
        "ok": result.get("ok"),
        "symbol": symbol,
        "statement_type": result.get("statement_type") or result.get("statement"),
        "provider": result.get("provider"),
        "source": result.get("source"),
        "upstream": result.get("upstream"),
        "row_count": len(rows),
        "latest_data_date": quality.get("latest_data_date"),
        "data_quality_keys": sorted(quality.keys()),
        "freshness_status": quality.get("freshness_status"),
        "warnings": warnings,
        "errors": errors,
        "primary_error": quality.get("primary_error"),
        "top_level_keys": sorted(result.keys()),
        "first_row_keys": sorted(first_row.keys()),
        "has_rows": bool(rows),
        "has_data_quality": bool(quality),
        "report_summary_compatibility": {
            "has_provider": bool(result.get("provider") or quality.get("provider")),
            "has_source": bool(result.get("source") or quality.get("source")),
            "has_data_quality": bool(quality),
            "has_latest_data_date": bool(quality.get("latest_data_date")),
            "has_warnings": bool(warnings),
            "has_primary_error": bool(quality.get("primary_error")),
        },
    }
    return summary


def write_report(results: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"get_financial_statements_fallback_output_inspection_{timestamp}.json"
    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": "scripts/inspect_get_financial_statements_fallback_output.py",
        "forced_primary_failure": FORCED_PRIMARY_FAILURE,
        "results": results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    statements = [item.strip().lower() for item in args.statement_types.split(",") if item.strip()]

    results: list[dict[str, Any]] = []
    for symbol in symbols:
        for statement_type in statements:
            summary = inspect_one(symbol, statement_type, timeout=args.timeout)
            results.append(summary)
            print(
                "OK={ok} symbol={symbol} statement={statement} provider={provider} "
                "source={source} upstream={upstream} rows={rows} latest={latest} "
                "freshness={freshness} has_dq={has_dq} compat={compat}".format(
                    ok=summary["ok"],
                    symbol=summary["symbol"],
                    statement=summary["statement_type"],
                    provider=summary["provider"],
                    source=summary["source"],
                    upstream=summary["upstream"],
                    rows=summary["row_count"],
                    latest=summary["latest_data_date"],
                    freshness=summary["freshness_status"],
                    has_dq=summary["has_data_quality"],
                    compat=summary["report_summary_compatibility"],
                )
            )
            print(f"top_level_keys={summary['top_level_keys']}")
            print(f"data_quality_keys={summary['data_quality_keys']}")
            print(f"first_row_keys={summary['first_row_keys'][:25]}")
            print(f"warnings={summary['warnings']}")
            print(f"errors={summary['errors']}")
            print(f"primary_error={summary['primary_error']}")

    if args.output_dir:
        report_path = write_report(results, (ROOT / args.output_dir).resolve())
        print(f"JSON report: {report_path}")

    failed = [
        item
        for item in results
        if not item["ok"] or not all(item["report_summary_compatibility"].values())
    ]
    print(f"Summary: {len(results) - len(failed)}/{len(results)} compatible")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
