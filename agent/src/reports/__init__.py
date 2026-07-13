"""Structured report builders for research workspace proofs."""

from src.reports.artifact_generator import generate_research_artifact
from src.reports.report_builder import ReportBuildError, build_research_report
from src.reports.financial_confidence import FinancialConfidenceError, extract_financial_confidence
from src.reports.tool_result_serializer import serialize_tool_result
from src.reports.trace_collector import (
    TraceCollection,
    build_research_report_from_trace_events,
    collect_tool_results_from_trace_events,
)

__all__ = [
    "ReportBuildError",
    "generate_research_artifact",
    "FinancialConfidenceError",
    "TraceCollection",
    "extract_financial_confidence",
    "build_research_report",
    "build_research_report_from_trace_events",
    "collect_tool_results_from_trace_events",
    "serialize_tool_result",
]
