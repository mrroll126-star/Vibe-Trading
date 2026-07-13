# Financial Data Confidence Extraction Design

## 1. Purpose

This contract defines a future Financial Confidence Extractor that turns normalized
`FinancialStatementsTool` output into auditable report fields. It covers only
`income`, `balance`, and `cashflow`; it does not change AgentLoop, providers,
loaders, Web UI, or runtime behavior.

```text
Tool output
  -> Financial Confidence Extractor
  -> financial_health + data_confidence + warnings
```

Financial confidence is about disclosed reporting periods. It must not reuse
intraday market-data freshness labels.

## 2. Financial Confidence Data Model

Each requested statement produces a record, even when it is missing, failed,
blocked, or not applicable. Metadata is never silently omitted.

```json
{
  "statement_type": "income",
  "status": "available",
  "provider": "a_stock_data",
  "source": "sina_financial_report",
  "upstream": "sina",
  "latest_period": "2026-03-31",
  "row_count": 3,
  "completeness": "sufficient",
  "quality_status": "reported_period_available",
  "reporting_period_status": "current_for_expected_cycle",
  "fallback_used": true,
  "primary_error": "primary_financials_unavailable",
  "warnings": ["primary_provider_unavailable", "a_stock_data_fallback_used"]
}
```

| Field | Rule | Ownership |
| --- | --- | --- |
| `statement_type` | `income`, `balance`, or `cashflow` | Tool request/result |
| `status` | `available`, `partial`, `missing`, `failed`, `blocked`, or `not_applicable` | Extractor |
| `provider`, `source`, `upstream` | Actual path that supplied usable rows | Tool output only |
| `latest_period` | Latest parsed report date | Normalized statement row only |
| `row_count` | Normalized usable-row count | Program calculated |
| `completeness`, `quality_status` | Usability/audit assessment | Extractor |
| `fallback_used`, `primary_error`, `warnings` | Primary/fallback outcome | Tool output plus extractor rule |

The Research Schema must contain:

```json
{
  "financial_health": {
    "status": "partial",
    "statement_level_confidence": [],
    "reporting_period": {},
    "freshness_policy": {},
    "fallback_status": {},
    "warnings": []
  },
  "data_confidence": { "financial_data": {} }
}
```

## 3. Three-Statement Contract

### Income

Expected fields where supplied: revenue/operating revenue, net profit, EPS, and
report date. `available` needs usable rows, a parseable period, provider, and
source. Missing period/source/provider or a required metric makes it `partial`.
The Agent may discuss revenue or profit only from reported values and periods.

### Balance

Expected fields where supplied: total assets, total liabilities, shareholder
equity, and report date. The same status rules apply. If assets, liabilities,
or equity are missing, the Agent must not claim a complete solvency or capital
structure assessment.

### Cash Flow

Expected fields where supplied: operating, investing, financing, and net cash
flow plus report date. If operating cash flow is missing, the Agent must not
infer cash-generation quality from profit alone.

## 4. Combined Financial Health

| Status | Rule |
| --- | --- |
| `available` | All three core statements are available or acceptably partial, with provider/source/period disclosed. |
| `partial` | At least one usable statement exists but any core statement is missing, failed, blocked, or materially incomplete. |
| `missing` | No usable core statement exists. |
| `blocked` | Guard or asset-routing policy prevented a financial request. |

`complete` for the MVP means income, balance, and cashflow all exist. News,
research reports, indicators, and market data do not alter this definition.

## 5. Provenance and Fallback

### Primary Success

Set `fallback_used=false`; retain the actual primary provider/source/upstream.
Do not label data as fallback merely because fallback capability exists.

### Primary Failure, Fallback Success

Set `fallback_used=true`, retain `provider=a_stock_data`,
`source=sina_financial_report`, and `upstream=sina` when those are supplied.
Add concise warnings `primary_provider_unavailable` and
`a_stock_data_fallback_used`. Preserve a safe primary error summary without
transport details or credentials.

### Primary and Fallback Failure

Set statement status to `failed`, preserve `financial_statement_unavailable`,
and produce no conclusion for that statement.

### Ineligible Asset

ETF, index, US/HK symbol, ambiguous code, and unverified Chinese name must not
run the current A-share fallback. Report `blocked` or `not_applicable`; do not
misrepresent this as a provider outage.

## 6. Reporting Period Policy

| Status | Meaning | Report behavior |
| --- | --- | --- |
| `current_for_expected_cycle` | Latest period is plausible for a normal reporting cycle. | State the exact period; allow period-bounded analysis. |
| `period_available_but_age_unassessed` | Date parses but expected-cycle policy cannot assess it. | Allow historical discussion and disclose the limitation. |
| `stale_for_expected_cycle` | Latest period materially lags the configured disclosure cycle. | Do not call it latest financial condition; warn. |
| `missing_period` | No parseable reporting period. | Do not call results latest; limit analysis. |
| `invalid_period` | Date is malformed or inconsistent. | Exclude from conclusions and warn. |

A future implementation may classify dates as Q1/H1/Q3/FY only when reliable.
It must keep the exact `latest_period` date as the source of truth. Filing
deadlines and grace windows are future configurable policy, not hard-coded now.

## 7. Agent Prohibited Behaviors

The Agent must not:

1. Infer missing revenue, profit, assets, liabilities, or cash flow.
2. Describe financial health as complete when a core statement is missing or materially incomplete.
3. Hide fallback usage or provider failure.
4. Call missing or age-unassessed data the latest financial condition.
5. Turn periodic financial figures into current-day facts.
6. Manufacture indicators, forecasts, target prices, or ratios without inputs.
7. Treat an `indicators` failure as proof that raw three-statement data is absent.

When cashflow is absent, for example, the report must explicitly state that
cash-conversion analysis cannot be made from verified data.

## 8. Schema Integration

The extractor runs after tool-result normalization and before AI interpretation:

```text
normalized statement rows + source metadata
  -> Financial Confidence Extractor
  -> financial_health.statements[]
  -> financial_health.statement_level_confidence[]
  -> financial_health.quality and warnings
  -> data_confidence.financial_data
  -> bounded AI financial summary and investment memo
```

Program-owned fields include provider, source, upstream, period, row count,
fallback state, status, and warnings. The LLM may write only bounded
interpretation after it receives those facts and limitations.

Example `data_confidence.financial_data`:

```json
{
  "status": "partial",
  "reporting_period": "2026-03-31",
  "providers": ["a_stock_data"],
  "sources": ["sina_financial_report"],
  "fallback_used": true,
  "warnings": []
}
```

## 9. Future Implementation Acceptance Criteria

Fixture-first tests must prove:

1. Primary success preserves actual source metadata and `fallback_used=false`.
2. Fallback success preserves provider/source/upstream, primary error disclosure, and `fallback_used=true`.
3. Missing/failed statements create explicit records and combined `partial` or `missing` status.
4. Missing period never becomes a latest-data claim.
5. Ineligible assets never enter the A-share fallback.
6. Both `financial_health` and `data_confidence` receive program-produced metadata.
7. AI input includes missing statements, period status, and fallback warnings.

## 10. Scope and Rollback

This is documentation only. A future extractor must be isolated in the
schema/post-processing layer, behind focused fixture tests. It must be possible
to disable that new path without changing `FinancialStatementsTool`, its
fallback, the provider chain, or raw tool output.

## 11. Recommended Next Step

Design the minimal fixture-first `FinancialConfidenceExtractor` implementation
and acceptance tests before producing a persisted `research_schema.json`
artifact or expanding a-stock-data to new data domains.

## 12. Fixture-first Proof Status (2026-07-13)

Implemented offline proof:

* `agent/src/reports/financial_confidence.py` provides the pure
  `extract_financial_confidence(...)` function.
* It accepts fixture/tool-like results for the three core statements and
  produces `financial_health`, `data_confidence.financial_data`, and
  de-duplicated warnings.
* It preserves primary/fallback provenance, reports missing provider/source or
  reporting period, and rejects non-stock asset types.
* `agent/tests/test_financial_confidence_extractor.py` covers complete,
  fallback, failed, missing, metadata-missing, reporting-period-missing, and
  index/ETF cases.

Boundary:

* The proof is not wired into `build_research_report`, trace collection, or
  AgentLoop yet.
* It does not call live providers or read runtime/configuration files.

## 13. Primary Envelope Normalization Proof (2026-07-13)

Implemented a fixture-only normalizer for the confirmed Eastmoney primary
financial envelope. It maps only existing `data[symbol].periods` rows into the
canonical `data[symbol]` row-list shape used by the report builder and
confidence extractor. `REPORT_DATE` becomes `report_date` only when present in
the source row; no values, dates, provider, or source facts are inferred.

The normalizer preserves supplied provenance and emits warnings for missing
provider, source, symbol data, periods, statement type, and reporting period.
Complete income/balance/cashflow fixtures produce complete financial confidence
and a complete artifact. This remains a standalone proof and is not connected
to AgentLoop, tools, provider routing, or live trace consumption.

## 14. Report Consumer Integration Proof (2026-07-13)

The normalizer is now consumed in the offline trace-to-report path after trace
collection and before report assembly. This keeps `report_builder` provider
agnostic: it receives only canonical statement results. Trace metadata is
retained as an internal consumer input so normalizer provenance uses verified
trace fields rather than inferred values.

Legacy canonical rows bypass normalization. Provider records remain separate;
the pipeline never combines primary and fallback rows. Normalizer failures are
non-blocking and become collection warnings. Fixture Eastmoney structured
payloads now produce complete three-statement confidence and a complete
artifact without AgentLoop or live data.

## 15. Real Trace Observation Consumer Support (2026-07-13)

The read-only schema and artifact observation scripts now resolve the optional
`structured_payload` trace sidecar alongside legacy `result`, `content`, and
`prompt` fields. After loading, the existing collector continues to prefer a
verified structured payload, then sends collected financial results through
the report-consumer normalizer before report assembly.

Compatibility rules remain explicit:

* Legacy canonical financial rows continue through the legacy path unchanged.
* A malformed structured envelope cannot block schema observation; it becomes
  a normalizer warning and results in partial or missing financial confidence.
* Missing income, balance, or cashflow remains a partial financial result.
* Observation never fills missing provider, source, upstream, or reporting
  period facts from inference.

The existing historical `300750.SZ` trace now exposes the Eastmoney periods
envelopes to the normalizer. It still correctly produces partial confidence:
the recorded payload has no provider value and the trace has no final-answer
event. This is a provenance gap in the existing trace, not a reason to invent
metadata or declare the financial data complete.

## 16. Primary Provenance Projection Fixture Proof (2026-07-13)

The fixture-first provenance projector now supplies the metadata the financial
confidence path needs without relying on legacy text: verified provider,
source, upstream, statement type, actual reporting periods, row count,
adapter-produced quality metadata, fallback status, primary error, and stable
warnings. It uses only structured payload rows and explicit execution context.

Three complete primary-statement fixtures produce complete confidence and a
complete artifact. Missing provider, source, or reporting period remains a
warning and produces partial confidence. Fallback fixtures retain the actual
fallback provenance and primary error. The projector is not yet called by the
runtime dual-write hook.
