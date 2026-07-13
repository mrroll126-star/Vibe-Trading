# Financial Confidence Integration Plan

## 1. Purpose

This plan defines how the existing pure `FinancialConfidenceExtractor` should
be connected to `build_research_report(...)` without changing AgentLoop,
providers, loaders, trace storage, or Web UI behavior.

The target is a controlled schema-only path:

```text
validated financial tool results
  -> FinancialConfidenceExtractor
  -> report_builder schema assembly
  -> financial_health + data_confidence.financial_data
```

Implementation is explicitly out of scope for this document.

## 2. Current State

Two independent modules now exist:

```text
trace_collector
  -> list[financial tool results]
  -> report_builder

financial_confidence
  -> {income, balance, cashflow} result mapping
  -> financial_health + data_confidence.financial_data + warnings
```

`report_builder.py` currently extracts statement facts and derives financial
confidence using its own local helpers. It mostly summarizes the first
statement for `data_confidence.financial_data`. The new extractor instead
creates one confidence record per core statement. Neither module currently
calls the other.

## 3. Integration Options

### Option A: Report Builder Directly Calls Extractor

`build_research_report(...)` converts its existing `financial_results` list
into a statement-type mapping, calls `extract_financial_confidence(...)`, then
uses the returned confidence object while assembling the final schema.

Advantages:

* Smallest code surface and lowest regression risk.
* Keeps existing trace collector and tool contracts unchanged.
* Preserves the current builder as the single schema assembly point.
* Easy fixture-first tests and easy rollback.

Trade-offs:

* The builder needs a small mechanical result-indexing helper.
* Builder tests need carefully updated expectations.

### Option B: Add a Separate Normalization Layer Before Builder

A new layer would convert all tool results into a common report-input object
before the builder and extractor see them.

Advantages:

* Clearer long-term canonical input contract.
* Can later normalize market, news, research reports, and other domains.

Trade-offs:

* Broader new abstraction before there is more than one real consumer.
* More migration and regression surface than the current MVP requires.

### Option C: Call Extractor Only in the Post-run Agent Artifact Pipeline

The post-processor would call the extractor after trace collection, while
`report_builder` remains unchanged.

Advantages:

* Limits the change to future artifact production.

Trade-offs:

* Creates two financial schema paths: direct builder proof versus post-run
  artifact path.
* Delays consistent confidence output for direct and fixture report proofs.

## 4. MVP Recommendation

Use Option A with a strict boundary:

```text
report_builder
  -> private mechanical index of financial result list by statement type
  -> FinancialConfidenceExtractor
  -> schema assembly only
```

The builder must not reimplement provider, fallback, reporting-period,
completeness, or warning rules. Those decisions belong only to the extractor.
The indexing helper may select the final tool result for each requested
statement type, preserving a documented duplicate-result rule.

Reason: it gives all current schema paths the same confidence contract while
leaving trace collection and AgentLoop untouched. Option B becomes appropriate
when at least one other report domain needs a reusable normalization layer.

## 5. Future Data Flow

```text
Trace
  -> trace_collector
  -> market result + list of financial results
  -> report_builder result index
  -> FinancialConfidenceExtractor
  -> report_builder
  -> structured Research Report
  -> future research_schema.json post-processor artifact
```

For direct tool proofs, the same flow begins at validated tool output instead
of a trace. The extractor must not read trace files, call providers, or inspect
the final answer.

## 6. Input and Output Contract

### Extractor Input

The integration adapter must provide only the core keys:

```json
{
  "income": {"ok": true, "statement_type": "income", "data": []},
  "balance": {"ok": true, "statement_type": "balance", "data": []},
  "cashflow": {"ok": false, "statement_type": "cashflow", "error": "missing"}
}
```

Each value is the original validated tool-result dictionary. The adapter must
not manufacture provider, source, upstream, rows, reporting period, or fallback
metadata. Missing statement types are represented by absent mapping keys so the
extractor emits an explicit missing record.

### Extractor Output

```json
{
  "financial_health": {
    "status": "complete|partial|missing",
    "statement_level_confidence": [],
    "reporting_period": {},
    "fallback_status": {},
    "warnings": []
  },
  "data_confidence": { "financial_data": {} },
  "warnings": []
}
```

The builder consumes these fields as program-owned financial facts. It may add
existing schema sections such as raw statement metrics and empty AI-summary
placeholders, but it may not downgrade, overwrite, or hide extractor warnings.

## 7. Report Builder Boundary

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `trace_collector` | Read trace events and expose raw tool results | Decide financial quality or fallback meaning |
| result-index adapter | Select/index `income`, `balance`, `cashflow` tool results mechanically | Invent missing metadata or call providers |
| `FinancialConfidenceExtractor` | Determine statement confidence, combined status, reporting-period status, fallback state, and warnings | Build whole report or generate narrative |
| `report_builder` | Assemble all report sections and place extractor output in schema | Duplicate extractor rules or ask LLM to fill financial metadata |
| AI interpretation | Write bounded narrative from facts and limitations | Invent figures, source, date, fallback, or confidence status |

## 8. Partial Schema Policy

| Situation | Statement confidence | `financial_health.status` | Report behavior |
| --- | --- | --- |
| All three core statements usable | All available | `complete` | Financial narrative may cover all three, bounded to reported periods. |
| Income missing/failed | Explicit missing/failed income | `partial` | No revenue/profit trend conclusion. |
| Balance missing/failed | Explicit missing/failed balance | `partial` | No complete solvency/capital-structure conclusion. |
| Cashflow missing/failed | Explicit missing/failed cashflow | `partial` | No cash-conversion conclusion. |
| All three absent/failed | Explicit records for all | `missing` | No financial-health conclusion. |
| Fallback used | Provider/source/upstream plus `fallback_used=true` | Same structural status | Show fallback disclosure in financial data confidence and warnings. |
| Provider/source missing | Statement `partial` with warning | `partial` | Do not present source as verified. |
| Reporting period missing | Statement `partial` with `missing_reporting_period` | `partial` | Do not call data latest. |

`indicators` remains outside the core three-statement completeness rule. Its
failure must not turn otherwise complete raw statements into `partial`.

## 9. Duplicate and Conflicting Result Policy

Real traces may contain repeated calls. The future indexing adapter should:

1. Keep results only for `income`, `balance`, and `cashflow`.
2. Prefer a successful result with usable rows over a later failed/empty retry.
3. If multiple usable results conflict on provider/source/period, select the
   one used by the recorded tool result chosen for the schema and append a
   `duplicate_financial_result_conflict` warning.
4. Preserve the extractor's no-invention rule; do not merge rows from different
   providers silently.

This rule should be fixture-tested before implementation because it controls
which financial fact becomes product data.

## 10. Fixture-first Test Strategy

No live data or AgentLoop is needed for the first integration change.

Required future tests:

1. Complete trace fixture -> collector -> builder -> extractor output has
   three statement confidence records and `financial_health.status=complete`.
2. One fallback statement preserves fallback provider/source/upstream and
   warning in both `financial_health` and `data_confidence.financial_data`.
3. Missing income, balance, and cashflow are tested separately; each creates
   the correct partial narrative boundary.
4. Provider/source and reporting-period omissions remain visible in the final
   builder schema.
5. Index/ETF direct report fixtures retain existing blocked behavior and never
   call the extractor for company financial confidence.
6. Duplicate financial result fixture follows the selected-result policy.
7. Existing report-builder, direct-tool, trace-fixture, and extractor suites
   remain green.

Acceptance is schema equality/assertion based. It must not depend on Markdown,
LLM output, a live run, or a Web UI.

## 11. Rollback Plan

The integration should be one narrow builder call and one result-index helper.
If it regresses existing schema proofs, remove the call and retain the current
builder logic and independent extractor module. No provider, fallback hook,
tool result, trace, or AgentLoop state needs rollback.

## 12. Implementation Gate

Implement only after the fixture contract and duplicate-result policy are
reviewed. The first implementation should not write `research_schema.json`;
it should only improve in-memory/direct schema proof output.

## 13. Fixture-first Integration Proof Status (2026-07-13)

Implemented as the recommended Option A:

* report_builder now mechanically indexes the three core statement results and
  calls the existing pure extractor for stock assets only.
* The builder merges extractor output into financial_health and uses
  extractor-owned data_confidence.financial_data.
* The trace collector remains unchanged, so its existing trace-to-report
  function now proves the full offline path: trace fixture, collector,
  extractor, builder, then schema.
* Index and ETF paths retain existing blocked-financial behavior and do not
  invoke company-statement confidence extraction.
* Duplicate indexing prefers a successful result with usable rows and never
  merges data from different providers.

Validation remains fixture-only. No real run, live data, production artifact,
AgentLoop, provider, loader, or Web UI path was changed.

## 14. Primary Envelope Consumer Integration Proof (2026-07-13)

The trace collector now passes collected financial records through the isolated
financial pipeline before calling the provider-agnostic report builder. The
pipeline recognizes the Eastmoney `data[symbol].periods` envelope, invokes the
pure normalizer, and preserves normalizer warnings as collection warnings.

Legacy row-list results bypass this path unchanged. Each provider result stays
independent; the pipeline does not merge primary and fallback rows. Fixture
tests confirm complete Eastmoney core statements yield complete confidence and
artifact output, while malformed envelopes remain non-blocking partial/missing
results with explicit warnings.

## 15. Primary Provenance Projection Fixture Proof (2026-07-13)

The new pure provenance projection helper sits before the existing consumer
path in fixture tests:

```text
structured payload + explicit execution metadata
  -> financial provenance projection
  -> trace-compatible structured payload and metadata
  -> collector -> financial pipeline -> report builder -> artifact
```

The report builder remains provider agnostic, the normalizer still owns only
row canonicalization, and the confidence extractor still decides completeness.
The projector is the sole producer of newly calculated row count and
reporting-period projection; it does not infer source/provider/upstream or
change the runtime dual-write path.

## 16. Default-off Runtime Producer Integration (2026-07-13)

The projector is now used by the financial-only runtime dual-write helper after
serializer success. The call site passes existing tool-call arguments and an
optional execution-metadata mapping. The consumer pipeline remains unchanged:

```text
TraceWriter event -> collector -> normalizer -> extractor -> builder -> artifact
```

Runtime tests prove complete artifacts only with explicit primary execution
metadata. In the actual current primary path, missing provider/upstream remains
an honest partial result. No runtime code infers these fields from tool name,
source text, current configuration, or legacy result prose.

## 17. Execution Metadata Producer Dependency (2026-07-13)

The extractor and report consumer are ready to consume explicit primary
provenance, but they cannot create it. The remaining upstream dependency is a
per-call producer in the financial execution branch, transported through the
registry without changing legacy tool text. This is intentionally separate from
financial confidence rules; see
`docs_local/PRIMARY_FINANCIAL_EXECUTION_METADATA_PRODUCER_DESIGN.md`.
