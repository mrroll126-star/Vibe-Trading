#!/usr/bin/env python3
"""One-off live smoke test for the candidate a-stock-data financial endpoint.

This script is deliberately outside AgentLoop and outside the provider chain.
It does not read ``agent/.env`` and does not require an LLM key.  It calls the
Sina financial-report endpoint described by the upstream a-stock-data Skill,
then passes the raw rows through Vibe-Trading's local normalizer to inspect
whether the raw shape is compatible with the future fallback adapter.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from src.adapters.a_stock_data.normalizer import normalize_a_stock_financials_result  # noqa: E402


SINA_FINANCIAL_URL = (
    "https://quotes.sina.cn/cn/api/openapi.php/"
    "CompanyFinanceService.getFinanceReport2022"
)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
STATEMENT_TO_SINA = {
    "income": "lrb",
    "balance": "fzb",
    "cashflow": "llb",
}
DATE_KEYS = ("报告期", "report_date", "reportDate", "date", "end_date", "endDate", "period")
SOURCE_KEYS = ("source", "provider", "upstream")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test candidate a-stock-data Sina financial rows."
    )
    parser.add_argument(
        "--symbols",
        default="600519.SH,300750.SZ",
        help="Comma-separated explicit A-share stock symbols.",
    )
    parser.add_argument(
        "--statements",
        default="income",
        help="Comma-separated statements: income,balance,cashflow.",
    )
    parser.add_argument("--num", type=int, default=3, help="Number of periods.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout seconds.")
    parser.add_argument("--sleep", type=float, default=1.2, help="Sleep between requests.")
    parser.add_argument(
        "--output-dir",
        default="local_reports",
        help="Ignored local directory for JSON smoke output.",
    )
    return parser.parse_args()


def normalize_symbol_for_sina(symbol: str) -> tuple[str, str | None]:
    cleaned = symbol.strip().upper()
    if not cleaned:
        return "", "empty_symbol"
    if not (cleaned.endswith(".SH") or cleaned.endswith(".SZ")):
        return "", "symbol_must_be_explicit_sh_or_sz"
    digits = cleaned.split(".", 1)[0]
    if not (len(digits) == 6 and digits.isdigit()):
        return "", "symbol_must_start_with_six_digits"
    return digits, None


def fetch_sina_financial_report(
    symbol: str,
    statement_type: str,
    *,
    num: int,
    timeout: float,
) -> list[dict[str, Any]]:
    code, error = normalize_symbol_for_sina(symbol)
    if error:
        raise ValueError(error)
    report_type = STATEMENT_TO_SINA.get(statement_type)
    if report_type is None:
        raise ValueError(f"unsupported statement_type: {statement_type}")

    prefix = "sh" if code.startswith("6") else "sz"
    params = {
        "paperCode": f"{prefix}{code}",
        "source": report_type,
        "type": "0",
        "page": "1",
        "num": str(num),
    }
    response = requests.get(
        SINA_FINANCIAL_URL,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    report_list = (
        payload.get("result", {})
        .get("data", {})
        .get("report_list", {})
        or {}
    )
    if not isinstance(report_list, dict):
        raise ValueError(f"unexpected report_list type: {type(report_list).__name__}")

    rows: list[dict[str, Any]] = []
    for period in sorted(report_list.keys(), reverse=True)[:num]:
        obj = report_list.get(period) or {}
        items = obj.get("data", []) if isinstance(obj, dict) else []
        rec = {"报告期": _format_period(period)}
        for item in items or []:
            if not isinstance(item, dict):
                continue
            title = item.get("item_title", "")
            if not title or item.get("item_value") is None:
                continue
            rec[str(title)] = item.get("item_value")
            tongbi = item.get("item_tongbi")
            if tongbi not in (None, ""):
                rec[f"{title}_同比"] = tongbi
        rows.append(rec)
    return rows


def _format_period(period: str) -> str:
    text = str(period)
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text


def summarize_one(symbol: str, statement_type: str, *, num: int, timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {
        "ok": False,
        "symbol": symbol,
        "statement_type": statement_type,
        "elapsed_sec": None,
        "raw_type": None,
        "row_count": 0,
        "sample_keys": [],
        "date_fields_detected": [],
        "source_fields_detected": [],
        "normalized_ok": False,
        "normalized_freshness_status": None,
        "normalized_latest_data_date": None,
        "error": None,
    }
    try:
        rows = fetch_sina_financial_report(symbol, statement_type, num=num, timeout=timeout)
        normalized = normalize_a_stock_financials_result(
            rows,
            symbol,
            source="sina_financial_report",
            upstream="a-stock-data",
            statement_type=statement_type,
        )
        sample_keys = sorted(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
        quality = normalized.get("_data_quality", {}).get(symbol, {})
        result.update(
            {
                "ok": bool(rows) and bool(normalized.get("ok")),
                "raw_type": type(rows).__name__,
                "row_count": len(rows),
                "sample_keys": sample_keys[:30],
                "date_fields_detected": [key for key in DATE_KEYS if key in sample_keys],
                "source_fields_detected": [key for key in SOURCE_KEYS if key in sample_keys],
                "normalized_ok": bool(normalized.get("ok")),
                "normalized_freshness_status": quality.get("freshness_status"),
                "normalized_latest_data_date": quality.get("latest_data_date"),
            }
        )
    except Exception as exc:  # noqa: BLE001 - smoke test records failures, not aborts
        result["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    finally:
        result["elapsed_sec"] = round(time.perf_counter() - started, 3)
    return result


def write_report(results: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"a_stock_data_smoke_{timestamp}.json"
    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": "scripts/smoke_a_stock_data_financials.py",
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "results": results,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    statements = [item.strip().lower() for item in args.statements.split(",") if item.strip()]
    output_dir = (ROOT / args.output_dir).resolve()

    results: list[dict[str, Any]] = []
    for symbol_index, symbol in enumerate(symbols):
        for statement_index, statement in enumerate(statements):
            if symbol_index or statement_index:
                time.sleep(max(0.0, args.sleep))
            result = summarize_one(symbol, statement, num=args.num, timeout=args.timeout)
            results.append(result)
            status = "OK" if result["ok"] else "FAILED"
            print(
                f"{status} {symbol} {statement}: rows={result['row_count']} "
                f"date={result['normalized_latest_data_date']} error={result['error'] or ''}"
            )

    report_path = write_report(results, output_dir)
    print(f"JSON report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
