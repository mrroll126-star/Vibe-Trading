from __future__ import annotations

import unittest

from src.reports import generate_research_artifact
from src.reports.financial_confidence import extract_financial_confidence
from src.reports.financial_normalizer import normalize_financial_statement_payload
from src.reports.financial_pipeline import normalize_financial_results_for_report
from src.reports.financial_provenance import (
    build_financial_provenance_enrichment,
    project_financial_provenance,
)


SYMBOL = "300750.SZ"


def primary_payload(statement_type: str, *, include_period: bool = True) -> dict:
    row = {"VALUE": 1}
    if include_period:
        row["REPORT_DATE"] = "2026-03-31"
    return {
        "ok": True,
        "statement": statement_type,
        "data": {SYMBOL: {"periods": [row, {**row, "REPORT_DATE": "2025-12-31"}]}},
    }


def primary_metadata(**overrides: object) -> dict:
    metadata = {
        "provider": "eastmoney",
        "source": "eastmoney_financial_report",
        "upstream": "eastmoney",
        "fallback_used": False,
        "primary_error": None,
    }
    metadata.update(overrides)
    return metadata


def market_event() -> dict:
    return {
        "type": "tool_result",
        "tool": "get_market_data",
        "status": "ok",
        "result": {
            "ok": True,
            "data": {SYMBOL: [{"date": "2026-07-10", "close": 200.0}]},
            "_data_quality": {
                SYMBOL: {
                    "provider": "fixture_market",
                    "source": "fixture_market_data",
                    "latest_data_date": "2026-07-10",
                    "warnings": [],
                }
            },
        },
    }


def projected_financial_event(statement_type: str, **metadata_overrides: object) -> dict:
    enrichment = build_financial_provenance_enrichment(
        payload=primary_payload(statement_type),
        tool_name="get_financial_statements",
        tool_args={"statement_type": statement_type},
        execution_metadata=primary_metadata(**metadata_overrides),
    )
    return {
        "type": "tool_result",
        "tool": "get_financial_statements",
        "status": "ok",
        "result": "legacy financial text",
        "structured_payload": enrichment["structured_payload"],
        "metadata": enrichment["metadata"],
    }


class FinancialProvenanceProjectionTests(unittest.TestCase):
    def test_primary_eastmoney_statements_project_complete_provenance(self) -> None:
        for statement_type in ("income", "balance", "cashflow"):
            with self.subTest(statement_type=statement_type):
                projection = project_financial_provenance(
                    payload=primary_payload(statement_type),
                    tool_name="get_financial_statements",
                    tool_args={"statement_type": statement_type},
                    execution_metadata=primary_metadata(),
                )

                self.assertEqual(projection["provider"], "eastmoney")
                self.assertEqual(projection["source"], "eastmoney_financial_report")
                self.assertEqual(projection["upstream"], "eastmoney")
                self.assertEqual(projection["statement_type"], statement_type)
                self.assertEqual(projection["reporting_period"]["latest"], "2026-03-31")
                self.assertEqual(projection["row_count"], 2)
                self.assertFalse(projection["fallback_status"]["used"])
                self.assertEqual(projection["data_quality"]["quality_status"], "available")
                self.assertEqual(projection["warnings"], [])

    def test_missing_provider_is_not_inferred(self) -> None:
        projection = project_financial_provenance(
            payload=primary_payload("income"),
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata=primary_metadata(provider=""),
        )

        self.assertEqual(projection["provider"], "")
        self.assertIn("financial_provider_missing", projection["warnings"])
        self.assertEqual(projection["data_quality"]["quality_status"], "partial")

    def test_missing_source_does_not_use_provider(self) -> None:
        projection = project_financial_provenance(
            payload=primary_payload("income"),
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata=primary_metadata(source=""),
        )

        self.assertEqual(projection["source"], "")
        self.assertNotEqual(projection["source"], projection["provider"])
        self.assertIn("financial_source_missing", projection["warnings"])

    def test_missing_reporting_period_warns(self) -> None:
        payload = primary_payload("income", include_period=False)
        payload["data"][SYMBOL]["periods"] = [{"VALUE": 1}]
        projection = project_financial_provenance(
            payload=payload,
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata=primary_metadata(),
        )

        self.assertEqual(projection["reporting_period"]["latest"], "")
        self.assertIn("missing_reporting_period", projection["warnings"])

    def test_fallback_preserves_primary_error_and_real_fallback_metadata(self) -> None:
        projection = project_financial_provenance(
            payload=primary_payload("income"),
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata={
                "provider": "a_stock_data",
                "source": "sina_financial_report",
                "upstream": "sina",
                "fallback_used": True,
                "primary_error": "primary_financials_unavailable",
            },
        )

        self.assertTrue(projection["fallback_status"]["used"])
        self.assertEqual(projection["fallback_status"]["primary_error"], "primary_financials_unavailable")
        self.assertEqual(projection["provider"], "a_stock_data")
        self.assertEqual(projection["source"], "sina_financial_report")
        self.assertIn("fallback_provider_used", projection["warnings"])

    def test_malformed_payload_is_nonblocking_and_partial(self) -> None:
        projection = project_financial_provenance(
            payload={"ok": True, "statement": "income", "data": {SYMBOL: {}}},
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata=primary_metadata(),
        )

        self.assertEqual(projection["row_count"], 0)
        self.assertEqual(projection["data_quality"]["quality_status"], "partial")
        self.assertIn("financial_rows_missing", projection["warnings"])

    def test_warnings_are_deduplicated_in_stable_order(self) -> None:
        payload = primary_payload("income")
        payload["warnings"] = ["source_warning", "source_warning"]
        projection = project_financial_provenance(
            payload=payload,
            tool_name="get_financial_statements",
            tool_args={"statement_type": "income"},
            execution_metadata=primary_metadata(warnings=["source_warning", "execution_warning"]),
            serializer_metadata={"warnings": ["execution_warning", "serializer_warning"]},
        )

        self.assertEqual(
            projection["warnings"],
            ["source_warning", "execution_warning", "serializer_warning"],
        )

    def test_enriched_projection_flows_to_normalizer_confidence_and_artifact(self) -> None:
        events = [market_event()]
        events.extend(projected_financial_event(statement) for statement in ("income", "balance", "cashflow"))
        events.append({"type": "answer", "content": "Fixture interpretation."})

        artifact = generate_research_artifact(
            run_id="provenance-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "complete")
        report = artifact["research_report"]
        self.assertEqual(report["financial_health"]["status"], "complete")
        self.assertEqual(report["data_confidence"]["financial_data"]["provider"], "eastmoney")
        self.assertEqual(report["data_confidence"]["financial_data"]["source"], "eastmoney_financial_report")

    def test_missing_provenance_flows_to_partial_artifact_with_warning(self) -> None:
        events = [market_event()]
        events.extend(
            projected_financial_event(statement, provider="")
            for statement in ("income", "balance", "cashflow")
        )
        events.append({"type": "answer", "content": "Fixture interpretation."})

        artifact = generate_research_artifact(
            run_id="missing-provenance-fixture",
            trace_events=events,
            input_symbol=SYMBOL,
            metadata={"generated_at": "2026-07-13T00:00:00+00:00"},
        )

        self.assertEqual(artifact["artifact_meta"]["status"], "partial")
        self.assertIn("provider_missing", artifact["research_report"]["data_confidence"]["warnings"])

    def test_projected_payload_normalizes_and_extracts_confidence(self) -> None:
        results = {}
        for statement_type in ("income", "balance", "cashflow"):
            enrichment = build_financial_provenance_enrichment(
                payload=primary_payload(statement_type),
                tool_name="get_financial_statements",
                tool_args={"statement_type": statement_type},
                execution_metadata=primary_metadata(),
            )
            normalized = normalize_financial_statement_payload(
                enrichment["structured_payload"],
                metadata=enrichment["metadata"],
            )
            results[statement_type] = normalized

        canonical, warnings = normalize_financial_results_for_report(list(results.values()))
        self.assertEqual(warnings, [])
        confidence = extract_financial_confidence(
            {result["statement_type"]: result for result in canonical}
        )
        self.assertEqual(confidence["financial_health"]["status"], "complete")


if __name__ == "__main__":
    unittest.main()
