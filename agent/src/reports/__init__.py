"""Structured report builders for research workspace proofs."""

from src.reports.report_builder import ReportBuildError, build_research_report
from src.reports.trace_collector import (
    TraceCollection,
    build_research_report_from_trace_events,
    collect_tool_results_from_trace_events,
)

__all__ = [
    "ReportBuildError",
    "TraceCollection",
    "build_research_report",
    "build_research_report_from_trace_events",
    "collect_tool_results_from_trace_events",
]
