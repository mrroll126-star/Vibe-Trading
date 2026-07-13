from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import src.agent.trace as trace_mod
from src.agent.trace import TraceWriter
from scripts.observe_real_trace_to_schema import observe_trace_to_schema, resolve_trace_source


SYMBOL = "600519.SH"


def market_result(symbol: str = SYMBOL) -> dict:
    return {
        "ok": True,
        "data": {symbol: [{"date": "2026-07-10", "close": 1500.5}]},
        "_data_quality": {
            symbol: {
                "provider": "mock_market_provider",
                "source": "mock_market_data",
                "latest_data_date": "2026-07-10",
                "warnings": [],
            }
        },
    }


def financial_result(statement: str, symbol: str = SYMBOL) -> dict:
    rows = {
        "income": [{"report_date": "2026-03-31", "revenue": 547.03, "net_profit": 281.54}],
        "balance": [{"report_date": "2026-03-31", "total_assets": 3000.0}],
        "cashflow": [{"report_date": "2026-03-31", "operating_cash_flow": 260.0}],
    }
    return {
        "ok": True,
        "provider": "a_stock_data",
        "source": "sina_financial_report",
        "upstream": "a-stock-data",
        "statement_type": statement,
        "period": "annual",
        "data": {symbol: rows[statement]},
        "_data_quality": {
            symbol: {
                "provider": "a_stock_data",
                "source": "sina_financial_report",
                "upstream": "a-stock-data",
                "latest_data_date": "2026-03-31",
                "warnings": ["a_stock_data_fallback_used"],
            }
        },
    }


def eastmoney_periods_payload(statement: str, symbol: str = SYMBOL) -> dict:
    return {
        "ok": True,
        "source": "eastmoney",
        "statement": statement,
        "period": "annual",
        "data": {symbol: {"periods": [{"REPORT_DATE": "2026-03-31", "VALUE": 1}]}},
    }


def eastmoney_metadata() -> dict:
    return {
        "provider": "eastmoney",
        "source": "eastmoney_financial_report",
        "upstream": "eastmoney",
    }


def write_trace(trace_dir: Path, events: list[dict]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )


def complete_events() -> list[dict]:
    events = [
        {"type": "start", "prompt": "Analyze 600519.SH"},
        {
            "type": "tool_result",
            "tool": "get_market_data",
            "status": "ok",
            "result": json.dumps(market_result(), ensure_ascii=False),
        },
    ]
    for statement in ("income", "balance", "cashflow"):
        events.append(
            {
                "type": "tool_result",
                "tool": "get_financial_statements",
                "status": "ok",
                "result": json.dumps(financial_result(statement), ensure_ascii=False),
            }
        )
    events.append({"type": "answer", "content": "Final answer placeholder."})
    return events


class RealTraceObservationTests(unittest.TestCase):
    def test_trace_path_fixture_to_observation_summary_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            trace_dir = Path(temp) / "trace"
            write_trace(trace_dir, complete_events())

            summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL, run_id="run1")

        self.assertTrue(summary["compatibility"]["can_read_trace"])
        self.assertTrue(summary["schema_generated"])
        self.assertEqual(summary["tool_result_count"], 4)
        self.assertEqual(summary["financial_statement_types_found"], ["balance", "cashflow", "income"])
        self.assertIn("financial_health", summary["schema_sections_present"])
        self.assertEqual(summary["data_confidence_summary"]["financial_provider"], "a_stock_data")

    def test_missing_trace_path_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing"
            summary = observe_trace_to_schema(trace_dir=missing, symbol=SYMBOL)

        self.assertFalse(summary["compatibility"]["can_read_trace"])
        self.assertFalse(summary["schema_generated"])
        self.assertIn("trace.jsonl not found", summary["error"])

    def test_offloaded_tool_result_payload_is_resolved(self) -> None:
        old_threshold = trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD
        trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = 8
        try:
            with tempfile.TemporaryDirectory() as temp:
                trace_dir = Path(temp) / "trace"
                trace = TraceWriter(trace_dir)
                trace.write_tool_result(
                    call_id="market1",
                    result=json.dumps(market_result(), ensure_ascii=False),
                    tool_name="get_market_data",
                    status="ok",
                    elapsed_ms=1,
                    iteration=1,
                )
                trace.write_tool_result(
                    call_id="income1",
                    result=json.dumps(financial_result("income"), ensure_ascii=False),
                    tool_name="get_financial_statements",
                    status="ok",
                    elapsed_ms=1,
                    iteration=1,
                )
                trace.write_text_entry(
                    {"type": "answer", "iter": 1},
                    field="content",
                    value="Final answer placeholder.",
                    offload_kind="answer",
                )
                trace.close()

                summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)
        finally:
            trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = old_threshold

        self.assertTrue(summary["compatibility"]["can_read_trace"])
        self.assertTrue(summary["schema_generated"])
        self.assertIn("income", summary["financial_statement_types_found"])

    def test_offloaded_structured_financial_payload_uses_normalizer_pipeline(self) -> None:
        old_threshold = trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD
        trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = 8
        try:
            with tempfile.TemporaryDirectory() as temp:
                trace_dir = Path(temp) / "trace"
                trace = TraceWriter(trace_dir)
                trace.write_tool_result(
                    call_id="market1",
                    result=json.dumps(market_result(), ensure_ascii=False),
                    tool_name="get_market_data",
                    status="ok",
                    elapsed_ms=1,
                    iteration=1,
                )
                for statement in ("income", "balance", "cashflow"):
                    trace.write_tool_result(
                        call_id=f"{statement}1",
                        result="legacy financial text",
                        tool_name="get_financial_statements",
                        status="ok",
                        elapsed_ms=1,
                        iteration=1,
                        enrichment={
                            "structured_payload": eastmoney_periods_payload(statement),
                            "metadata": eastmoney_metadata(),
                        },
                    )
                trace.write_text_entry(
                    {"type": "answer", "iter": 1},
                    field="content",
                    value="Final answer placeholder.",
                    offload_kind="answer",
                )
                trace.close()

                summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)
        finally:
            trace_mod.TOOL_RESULT_OFFLOAD_THRESHOLD = old_threshold

        self.assertTrue(summary["schema_generated"])
        self.assertEqual(summary["financial_statement_types_found"], ["balance", "cashflow", "income"])
        self.assertEqual(summary["data_confidence_summary"]["financial_provider"], "eastmoney")
        self.assertEqual(summary["data_confidence_summary"]["financial_source"], "eastmoney_financial_report")

    def test_trace_with_no_tool_results_reports_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            trace_dir = Path(temp) / "trace"
            write_trace(trace_dir, [{"type": "answer", "content": "No tools."}])

            summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)

        self.assertTrue(summary["compatibility"]["can_read_trace"])
        self.assertFalse(summary["compatibility"]["has_tool_results"])
        self.assertFalse(summary["schema_generated"])
        self.assertIn("tool_results_missing_from_trace", summary["collector_warnings"])

    def test_trace_with_partial_financial_results_builds_partial_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            trace_dir = Path(temp) / "trace"
            write_trace(
                trace_dir,
                [
                    complete_events()[0],
                    complete_events()[1],
                    {
                        "type": "tool_result",
                        "tool": "get_financial_statements",
                        "status": "ok",
                        "result": json.dumps(financial_result("income"), ensure_ascii=False),
                    },
                    {"type": "answer", "content": "Partial financial answer."},
                ],
            )

            summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)

        self.assertTrue(summary["schema_generated"])
        self.assertEqual(summary["financial_statement_types_found"], ["income"])
        self.assertFalse(summary["compatibility"]["has_required_financial_results"])
        self.assertIn("balance_statement_missing", summary["collector_warnings"])

    def test_malformed_structured_financial_payload_keeps_schema_with_warning(self) -> None:
        malformed = eastmoney_periods_payload("income")
        malformed["data"] = {SYMBOL: {}}
        with tempfile.TemporaryDirectory() as temp:
            trace_dir = Path(temp) / "trace"
            write_trace(
                trace_dir,
                [
                    complete_events()[0],
                    complete_events()[1],
                    {
                        "type": "tool_result",
                        "tool": "get_financial_statements",
                        "status": "ok",
                        "result": "legacy financial text",
                        "structured_payload": malformed,
                        "metadata": eastmoney_metadata(),
                    },
                    {"type": "answer", "content": "Partial financial answer."},
                ],
            )
            summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)

        self.assertTrue(summary["schema_generated"])
        self.assertIn("financial_normalizer:income:missing_periods", summary["collector_warnings"])

    def test_final_answer_missing_still_attempts_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            trace_dir = Path(temp) / "trace"
            events = [event for event in complete_events() if event.get("type") != "answer"]
            write_trace(trace_dir, events)

            summary = observe_trace_to_schema(trace_dir=trace_dir, symbol=SYMBOL)

        self.assertFalse(summary["has_final_answer"])
        self.assertTrue(summary["schema_generated"])
        self.assertIn("final_answer_missing_from_trace", summary["collector_warnings"])

    def test_resolve_trace_source_does_not_guess_when_missing_ids(self) -> None:
        trace_dir, meta = resolve_trace_source()
        self.assertIsNone(trace_dir)
        self.assertEqual(meta["trace_source"], "")


if __name__ == "__main__":
    unittest.main()
