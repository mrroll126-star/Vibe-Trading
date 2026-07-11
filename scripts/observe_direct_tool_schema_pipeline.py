#!/usr/bin/env python3
"""Observe FinancialStatementsTool -> Research Report Schema pipeline.

This controlled proof calls the official ``FinancialStatementsTool`` path with
in-process mocked primary failure and mocked a-stock-data fallback rows. It then
passes the tool output into ``build_research_report``.

It does not enter AgentLoop, start Web UI, call live providers, read
``agent/.env``, or change provider chains.
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

from src.reports import build_research_report  # noqa: E402
from src.tools.financial_statements_tool import FinancialStatementsTool  # noqa: E402


SYMBOL = "600519.SH"
STATEMENTS = ("income", "balance", "cashflow")
FORCED_PRIMARY_FAILURE = {
    "ok": False,
    "error": "forced_primary_failure_for_schema_pipeline",
    "data": [],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Controlled FinancialStatementsTool -> report schema proof."
    )
    parser.add_argument("--symbol", default=SYMBOL, help="Explicit stock symbol. Default: 600519.SH")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional ignored local directory for JSON output, e.g. local_reports.",
    )
    return parser.parse_args()


def mock_market_result(symbol: str) -> dict[str, Any]:
    return {
        "ok": True,
        "data": {
            symbol: [
                {
                    "date": "2026-07-10",
                    "close": 1500.5,
                    "change_pct": 1.2,
                    "volume": 1000000,
                    "turnover": 1500500000,
                }
            ]
        },
        "_data_quality": {
            symbol: {
                "provider": "mock_market_provider",
                "source": "mock_market_data",
                "latest_data_date": "2026-07-10",
                "freshness_status": "fresh",
                "warnings": [],
            }
        },
    }


def mock_fallback_payload(symbol: str, statement: str) -> dict[str, Any]:
    rows_by_statement = {
        "income": [{"报告期": "2026-03-31", "营业收入": 547.03, "净利润": 281.54, "基本每股收益": 21.76}],
        "balance": [{"报告期": "2026-03-31", "总资产": 3000.0, "总负债": 500.0}],
        "cashflow": [{"报告期": "2026-03-31", "经营活动现金流": 260.0}],
    }
    return {
        "ok": True,
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "data": rows_by_statement.get(statement, []),
    }


def execute_financial_tool(symbol: str, statement: str) -> dict[str, Any]:
    def _mock_fetch(symbol_arg: str, statement_type: str | None = None, **_: Any) -> dict[str, Any]:
        return mock_fallback_payload(symbol_arg, statement_type or statement)

    with patch.dict(os.environ, {"VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER": "1"}, clear=False):
        with patch(
            "src.tools.financial_statements_tool._fetch_eastmoney_statement",
            return_value=FORCED_PRIMARY_FAILURE,
        ):
            with patch("src.tools.financial_statements_tool.fetch_a_stock_financials", side_effect=_mock_fetch):
                text = FinancialStatementsTool().execute(
                    code=symbol,
                    statement=statement,
                    period="annual",
                )
    return json.loads(text)


def build_pipeline_report(symbol: str) -> dict[str, Any]:
    financial_results = [execute_financial_tool(symbol, statement) for statement in STATEMENTS]
    return build_research_report(
        input_symbol=symbol,
        market_result=mock_market_result(symbol),
        financial_results=financial_results,
        interpretation={
            "thesis": "Placeholder thesis generated from validated schema facts.",
            "bull_case": ["Placeholder bull case; no numeric facts invented."],
            "bear_case": ["Placeholder bear case; no numeric facts invented."],
            "key_risks": ["Placeholder risk based on available data confidence."],
            "monitor_items": ["Monitor next reporting period and data-source warnings."],
        },
        run_id="direct-tool-schema-pipeline-proof",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        provider="none",
        model="none",
    )


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    financial = report.get("financial_health", {})
    statements = financial.get("statements") if isinstance(financial, dict) else []
    confidence = report.get("data_confidence", {})
    financial_confidence = confidence.get("financial_data") if isinstance(confidence, dict) else {}
    warnings = confidence.get("warnings") if isinstance(confidence, dict) else []
    return {
        "has_research_meta": isinstance(report.get("research_meta"), dict),
        "has_symbol": isinstance(report.get("symbol"), dict),
        "has_market_snapshot": isinstance(report.get("market_snapshot"), dict),
        "has_financial_health": isinstance(financial, dict),
        "has_data_confidence": isinstance(confidence, dict),
        "has_limitations": isinstance(report.get("limitations"), dict),
        "statement_count": len(statements) if isinstance(statements, list) else 0,
        "provider": financial_confidence.get("provider") if isinstance(financial_confidence, dict) else None,
        "source": financial_confidence.get("source") if isinstance(financial_confidence, dict) else None,
        "period_end_date": financial_confidence.get("period_end_date") if isinstance(financial_confidence, dict) else None,
        "warnings": warnings if isinstance(warnings, list) else [],
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"direct_tool_schema_pipeline_{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    report = build_pipeline_report(args.symbol)
    checks = validate_report(report)

    print(f"symbol={report['symbol']['normalized_symbol']}")
    print(f"financial_status={report['financial_health']['status']}")
    print(f"statement_count={checks['statement_count']}")
    print(f"provider={checks['provider']}")
    print(f"source={checks['source']}")
    print(f"period_end_date={checks['period_end_date']}")
    print(f"warnings={checks['warnings']}")

    if args.output_dir:
        path = write_report(report, (ROOT / args.output_dir).resolve())
        print(f"JSON report: {path}")

    required = (
        checks["has_research_meta"]
        and checks["has_symbol"]
        and checks["has_market_snapshot"]
        and checks["has_financial_health"]
        and checks["has_data_confidence"]
        and checks["has_limitations"]
        and checks["statement_count"] == 3
        and checks["provider"] == "a_stock_data"
        and checks["source"] == "sina_financial_report"
        and bool(checks["period_end_date"])
        and bool(checks["warnings"])
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())
