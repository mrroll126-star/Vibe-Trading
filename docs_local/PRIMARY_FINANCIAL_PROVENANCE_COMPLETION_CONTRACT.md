# Primary Financial Provenance Completion Contract

## 1. Purpose

This contract defines the verified provenance that a primary
`get_financial_statements` result must carry when structured tool tracing is
enabled. Its purpose is to let the existing post-processing path consume facts
mechanically:

```text
structured tool result
  -> trace_collector
  -> financial_pipeline
  -> FinancialConfidenceExtractor
  -> report_builder
  -> artifact_generator
```

The contract completes trace metadata; it does not change a provider result,
select a provider, infer financial facts, or turn an unavailable field into a
claim of completeness.

## 2. Current Finding

The observed primary Eastmoney envelope contains a recoverable
`data[symbol].periods` structure, a source label, statement type, and actual
period rows. The financial normalizer can convert those rows to the canonical
shape.

The same trace does not consistently include `provider`, `upstream`, or
`_data_quality`. Consequently, the confidence extractor correctly emits
`provider_missing` and the artifact remains `partial`. The absence must remain
visible until a verified runtime producer supplies the fields below.

## 3. Contract Scope

Applies only to a structured `tool_result` for:

```text
tool_name = get_financial_statements
```

and initially to primary provider results for confirmed stock symbols. It is
compatible with the existing fallback result shape, but it does not expand
fallback eligibility or add support for indicators, ETF, index, US, or HK
financial statements.

This is a versioned trace-consumption contract, not a replacement for the
legacy human-readable result supplied to the LLM.

## 4. Required Dual-write Envelope

The trace event retains the legacy text result and adds verified structured
facts when `VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE=1`:

```json
{
  "type": "tool_result",
  "tool": "get_financial_statements",
  "status": "ok",
  "result": "legacy human-readable result",
  "structured_payload": {},
  "human_summary": "Structured result available for get_financial_statements.",
  "metadata": {
    "provider": "eastmoney",
    "source": "eastmoney_financial_report",
    "upstream": "eastmoney",
    "statement_type": "income",
    "reporting_period": "2026-03-31",
    "row_count": 12,
    "data_quality": {},
    "fallback_status": {
      "fallback_used": false,
      "primary_error": ""
    },
    "warnings": []
  },
  "structured_trace_warnings": []
}
```

`structured_payload` remains the provider envelope copied from the tool
result. `metadata` is the compact, verified provenance projection used by
trace consumers. No consumer should reconstruct these facts from `result` or
`human_summary`.

## 5. Field Contract

| Field | Required semantics | Accepted producer source | Missing behavior |
| --- | --- | --- | --- |
| `provider` | Adapter/provider identity, e.g. `eastmoney` or `a_stock_data` | Explicit tool result field or known adapter-owned execution context | Empty; emit `provider_missing`; statement is partial. |
| `source` | Dataset/endpoint identity, e.g. `eastmoney_financial_report` | Explicit tool result/source constant owned by the adapter | Empty; emit `source_missing`; statement is partial. |
| `upstream` | External upstream identity, e.g. `eastmoney` or `sina` | Explicit tool result field or adapter-owned upstream constant | Empty is allowed but warned as `upstream_missing`; do not substitute provider. |
| `statement_type` | One requested statement: `income`, `balance`, or `cashflow` | Validated tool argument/result field | Empty; emit `missing_statement_type`; do not classify the rows. |
| `reporting_period` | Latest actual period in returned rows | Existing normalized period field, such as `REPORT_DATE` | Empty; emit `missing_reporting_period`; never call it latest. |
| `row_count` | Count of actual returned period rows | Program count after envelope normalization | `0` when no rows; emit statement-missing/empty warning. |
| `data_quality` | Provider-reported/adapter-produced quality metadata | Existing `_data_quality`, preserved without narrative synthesis | `{}` plus `metadata_data_quality_missing`; never create a quality status from date alone. |
| `fallback_status` | Whether this result is primary or fallback, including a primary error only if already reported | Existing fallback flags/errors in the result | `fallback_used=false` only when the executing branch is known primary; otherwise status is `unknown`. |
| `warnings` | Deduplicated machine warnings from provider, adapter, normalization, and trace serialization | Existing warning lists only | Empty list is valid; do not suppress known warnings. |

## 6. Source Precedence and Non-inference Rules

For every field, the producer follows this precedence:

1. A verified explicit field in the structured tool result.
2. Verified adapter execution context owned by the same code path.
3. Verified normalized row facts, only for `reporting_period` and `row_count`.
4. Missing field plus an explicit warning.

The following are prohibited:

* Deriving `provider` from a source string such as `eastmoney`.
* Treating an endpoint name as `upstream` without an adapter-owned mapping.
* Inferring a reporting period from the current date, a prompt, or market data.
* Treating a non-empty payload as a fresh or complete financial statement.
* Turning a fallback into a primary success, or hiding a recorded primary
  error.
* Parsing the legacy human summary or LLM text to recover a number, date, or
  provenance field.

## 7. Canonical Consumer Input

After `financial_pipeline` normalizes a provider envelope, each core statement
must be consumable as the following canonical record:

```json
{
  "ok": true,
  "statement_type": "income",
  "provider": "eastmoney",
  "source": "eastmoney_financial_report",
  "upstream": "eastmoney",
  "data": {"300750.SZ": [{"report_date": "2026-03-31"}]},
  "_data_quality": {
    "300750.SZ": {
      "provider": "eastmoney",
      "source": "eastmoney_financial_report",
      "upstream": "eastmoney",
      "latest_data_date": "2026-03-31",
      "reporting_period": "2026-03-31",
      "warnings": []
    }
  },
  "fallback_used": false,
  "warnings": []
}
```

The normalizer may map an existing `REPORT_DATE` to `report_date`, but may not
invent a date. It must preserve explicit provenance from trace metadata.

## 8. Fallback Status Contract

| Execution outcome | `fallback_status.fallback_used` | Required warning/disclosure |
| --- | --- | --- |
| Primary succeeds | `false` | No fallback warning. |
| Primary fails and verified fallback succeeds | `true` | `fallback_provider_used`; preserve existing `primary_error` when present. |
| Primary fails and fallback is not eligible or fails | `false` or `unknown` according to known branch state | Preserve the failure and do not claim financial availability. |
| Legacy trace with no branch marker | `unknown` | `fallback_status_unknown`; do not assume primary. |

`FinancialConfidenceExtractor` uses `fallback_used` as a disclosure property,
not as a quality downgrade by itself. Provenance or period absence continues to
produce partial confidence.

## 9. Consumer Responsibilities

### Trace collector

* Prefer a resolved `structured_payload` over legacy text.
* Attach trace metadata without overwriting explicit payload fields.
* Preserve malformed or missing metadata as warnings.

### Financial pipeline

* Detect only recognized provider envelope shapes.
* Convert verified period rows to canonical rows.
* Preserve provenance and warnings; do not merge competing providers.

### FinancialConfidenceExtractor

* Determine complete/partial/missing from three statement records and their
  verified metadata.
* Treat missing provider/source/period as partial rather than complete.
* Keep fallback status and primary errors visible.

### Report builder and artifact generator

* Consume canonical financial facts only.
* Place provenance in `financial_health` and
  `data_confidence.financial_data`.
* Mark the artifact partial when core confidence or final-answer requirements
  are incomplete; do not use artifact status to conceal warnings.

## 10. Status Semantics

| Status | Meaning |
| --- | --- |
| `complete` | Income, balance, and cashflow have rows, provider, source, and reporting period; all required facts are verified. |
| `partial` | At least one core statement is present, but a statement, provenance field, reporting period, or final-answer requirement is missing. |
| `missing` | No usable core financial statement is available. |
| `failed` | Artifact/report assembly itself cannot be completed. |

`unknown` is valid for individual metadata such as fallback branch state. It
must not be promoted to `complete`.

## 11. Feature Flag and Rollout

The existing runtime trace feature remains default off:

```text
VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE=0
```

Proposed rollout after implementation:

1. Add fixture tests for the complete primary provenance projection.
2. Enable only financial trace enrichment in a controlled local run.
3. Observe the trace through the existing read-only schema/artifact scripts.
4. Confirm every three-statement record is mechanically complete or visibly
   partial.
5. Keep legacy text and flag-off trace behavior unchanged throughout.

## 12. Acceptance Criteria

An implementation may be accepted only when fixture tests prove:

1. Primary income, balance, and cashflow records preserve all contract fields.
2. Fallback records preserve `fallback_used`, source, upstream, and any
   reported primary error.
3. Missing provider/source/period/data-quality fields become warnings and do
   not produce complete confidence.
4. A malformed provider envelope cannot block legacy tool execution or trace
   writing.
5. The collector, normalizer, extractor, report builder, and artifact
   generator consume the same canonical records without regex/LLM recovery.
6. Flag-off traces remain byte-shape compatible with the current legacy
   `tool_result` event contract.

## 13. Non-goals

This contract and its runtime integration do not:

* modify FinancialStatementsTool, TraceWriter, provider routing, loaders, or Web UI;
* run a new Agent task or call a live provider;
* create a production `research_schema.json` artifact;
* expand financial support to indicators, valuation metrics, or other assets;
* normalize unrelated market, news, or research-report results.

## 14. Fixture-first Projection Proof Status (2026-07-13)

Implemented an offline `financial_provenance` helper with two pure functions:

* `project_financial_provenance(...)` projects explicit structured payload,
  execution-context, and serializer metadata facts into the contract envelope.
* `build_financial_provenance_enrichment(...)` demonstrates the future runtime
  producer boundary by returning an enriched structured payload plus compact
  trace metadata, without changing the current runtime hook.

The proof covers complete primary Eastmoney income, balance, and cashflow
fixtures; missing provider/source/period cases; fallback provenance; malformed
payloads; stable warning de-duplication; and the full canonical consumer path.
Only existing structured rows contribute report periods and row count. The
normalizer now preserves explicit fallback status, primary error, and payload
warnings while canonicalizing rows.

At the fixture-proof stage, `runtime_dual_write.py`, AgentLoop,
FinancialStatementsTool, TraceWriter, and legacy LLM text had not changed.

## 15. Default-off Runtime Integration Status (2026-07-13)

The existing financial-only runtime dual-write hook now calls the projector
after serializer success and before trace enrichment is written. AgentLoop
passes only already-available tool-call `arguments` and an optional
`execution_metadata` mapping when one exists; neither layer derives a provider
from the tool name, payload shape, or configured default.

Flag-off events retain their legacy shape exactly. With the flag enabled,
projected facts occupy the existing trace `metadata` and enriched structured
payload; no second, competing provenance representation was added. Serializer
or projector failure stays trace-only and cannot block the legacy tool result,
LLM context, or Agent response.

The current real primary tool envelope has source, statement, and period rows,
but does not expose provider/upstream execution facts. It therefore remains
partial unless a future execution layer supplies verified metadata. The new
runtime integration proves complete behavior only with explicit fixture
execution metadata; it does not manufacture that metadata in production.

## 16. Execution Metadata Producer Design (2026-07-13)

The remaining primary-provenance blocker is now explicitly assigned to a
per-call financial execution metadata producer. `FinancialStatementsTool` is
the recommended producer because it owns actual primary/fallback branch
selection; ToolRegistry and AgentLoop must only transport an immutable result
wrapper. The detailed contract is in
`docs_local/PRIMARY_FINANCIAL_EXECUTION_METADATA_PRODUCER_DESIGN.md`.

Current `tc.execution_metadata` is a defensive optional read, not a
production-populated field. The next implementation must not mutate the
LLM-originated tool-call object or infer facts in a registry/consumer.

## 17. Fixture-first Transport Proof Status (2026-07-13)

The execution-metadata transport is now proven with an immutable per-call
wrapper. The additive registry API preserves the old string interface, and
AgentLoop passes returned metadata explicitly in both serial and parallel
paths. This proves transport only: real primary facts remain absent until
`FinancialStatementsTool` produces them.
