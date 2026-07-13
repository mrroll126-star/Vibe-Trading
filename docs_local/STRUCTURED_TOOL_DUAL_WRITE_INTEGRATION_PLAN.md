# Structured Tool Result Dual-write Integration Plan

## 1. Purpose

Define how future runtime instrumentation can persist a verified structured
tool payload beside the current human-readable tool-result text. The objective
is to make future traces consumable by report schema and artifact processors
without changing Agent planning, LLM context, Web UI behavior, provider order,
loader behavior, or tool public interfaces.

This is a design-only plan. No runtime code is changed by this document.

## 2. Current Flow Analysis

### Result generation

`BaseTool.execute(...)` is a string-returning interface. `ToolRegistry.execute`
returns the tool string or a JSON-formatted registry exception. In both serial
and parallel execution paths, AgentLoop obtains `(result, elapsed_ms)` and
funnels it into `_finalize_tool_result(...)`.

### LLM context

`_finalize_tool_result(...)` truncates the original `result` and calls
`ContextBuilder.format_tool_result(...)`. This creates the existing tool-role
message consumed by the next model turn. This input must remain byte-for-byte
behaviorally equivalent during dual-write rollout.

### Trace capture

The same finalization method redacts the result via `_redact_trace_result(...)`
and calls `TraceWriter.write_tool_result(...)`. `TraceWriter` stores one text
field named `result`, inline or as a text sidecar, together with tool name,
call id, status, elapsed time, iteration, and preview. Tool arguments are
already recorded separately in preceding `tool_call` events.

### Recommended minimum insertion point

The future adapter runs after trace redaction and immediately before
`TraceWriter.write_tool_result(...)`, as a best-effort trace-only side branch.
It receives the allowlisted tool name, the redacted legacy result, the
redacted arguments/call context, status, and elapsed time. It must not replace
the result passed to LLM context or the legacy trace text field.

To make argument association explicit, the future implementation may either
pass the already-redacted args into finalization or join them by `call_id` from
the preceding event. Passing redacted args is preferred: it makes each v1
tool-result event self-contained while retaining the original `tool_call`.

## 3. Recommended Dual-write Architecture

```text
Tool execution
  -> legacy result string
  -> existing LLM context: legacy result (unchanged)
  -> redacted legacy trace result
  -> Structured Result Adapter (best effort, flag-gated)
       -> structured_payload / metadata / warnings
  -> TraceWriter
       -> legacy result + optional structured fields
```

The adapter is `serialize_tool_result(...)` from the fixture proof. It parses
only a complete existing JSON object or mapping; it never asks an LLM, scrapes
rendered prose, or derives financial facts from `human_summary`.

With the flag enabled, a v1 `tool_result` adds:

* `trace_schema_version: "tool_result.v1"`;
* `tool_name` and redacted `args` (while retaining legacy `tool` and `call_id`);
* `structured_payload` or a validated JSON sidecar path;
* `human_summary`, bounded and safe for history display;
* `metadata` containing provider, source, upstream, data quality, timestamps,
  and payload status;
* `structured_trace_warnings`.

The pre-existing `result`, preview, status, timing, and text sidecar behavior
remain present. The structured payload is trace/audit data only; it is not a
new LLM prompt channel.

## 4. Feature Flag Strategy

Proposed flag:

```text
VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE=0
```

Default is disabled. When unset, invalid, or `0`, no serializer runs and
`TraceWriter` writes the same legacy event shape as before. When explicitly
`1`, only allowlisted tools add structured trace fields.

Initial allowlist:

* `get_financial_statements`

The flag affects trace enrichment and future post-processing only. It must not
alter tool invocation, guard decisions, provider fallback, returned text,
Agent response, Web UI response, or existing run-history readers.

## 5. Failure Strategy

Structured enrichment is strictly non-blocking.

| Condition | LLM context | Legacy trace | Structured trace fields |
| --- | --- | --- | --- |
| Serializer succeeds | unchanged legacy text | unchanged legacy text | payload and metadata added |
| Legacy text/non-JSON | unchanged legacy text | unchanged legacy text | `structured_payload: null`, `legacy_unstructured_result` |
| Serializer exception | unchanged legacy text | unchanged legacy text | `structured_payload: null`, `structured_payload_unavailable` |
| Sidecar write/validation failure | unchanged legacy text | unchanged legacy text | safe warning; no unsafe path |

Errors must be caught at the trace branch. They are audit warnings, not Agent
tool failures. The trace status continues to describe tool execution, while
payload availability is recorded separately in metadata/warnings.

## 6. Rollout Plan

### Phase 1: fixture dual-write proof

Completed. Serializer fixtures prove that market and financial JSON envelopes
can produce trace-compatible payloads and complete artifacts, while legacy
text remains unavailable.

Completed implementation proof: a dual-write event now retains legacy result
text beside the serializer payload in fixtures. The collector prefers a valid
`structured_payload` and falls back to legacy `result`, preserving historical
trace compatibility. Complete market plus income/balance/cashflow fixtures
produce a complete artifact; serializer failure and unsupported tools retain a
valid legacy event with trace-only warnings.

### Phase 2: financial tool only

Completed as an MVP. `get_financial_statements` now has a default-off,
trace-only enrichment branch after result redaction. The legacy return string
and LLM context remain unchanged. Flag-off events keep the legacy shape;
flag-on events add v1 fields only for the financial tool. Small structured JSON
payloads remain JSON objects in trace JSONL; large payloads use the existing
safe sidecar resolution pattern.

Covered fixture tests verify inline financial provenance, legacy behavior when
the flag is off, serializer-failure isolation, collector/report-builder
financial confidence, and non-financial-tool non-enrichment. No real Agent run
was used.

### Phase 3: market tool

Extend the same trace-only path to `get_market_data`, including its
`_data_quality` contract. Do not change provider chain or freshness behavior.

### Phase 4: controlled real-trace validation

Run one controlled research task with the flag enabled, then use the existing
observation script to confirm three-statement confidence, provenance, period,
data-quality, warnings, and artifact completeness. Keep production artifact
writing disabled.

Observation on 2026-07-13:

* Controlled CLI run `20260713_122810_49_b5872e` wrote structured payloads for
  income, balance, cashflow, and indicators with the runtime flag enabled.
* The payloads preserve the primary Eastmoney envelope and twelve available
  periods per core statement. No shell tool event was recorded.
* The existing report builder expects row lists, while this primary envelope
  stores rows at `data[symbol].periods`. It therefore reports financial data as
  missing despite the trace payload being recoverable.
* The existing observation scripts also need `structured_payload` added to
  their offload resolver field allowlist. This is an observation-consumer gap,
  not a failure of trace enrichment.

## 7. Test and Acceptance Plan

Before a real run:

* Flag unset/`0`: legacy trace event has no v1 fields and Agent-facing text is
  unchanged.
* Flag `1`: allowlisted valid JSON creates a v1 payload; legacy text remains.
* Non-JSON result and serializer exception do not block a successful tool call.
* Inline and offloaded structured payloads resolve to identical collector
  inputs, with safe path validation.
* Redaction applies to both structured payload and human summary.

Controlled real-run acceptance:

* `get_financial_statements` trace events contain recoverable income, balance,
  and cashflow payloads plus source, provider, upstream, reporting period,
  fallback, and data-quality facts.
* The resulting artifact can be `complete` or honestly `partial` according to
  real source availability, but must not report statement data as missing
  solely because the trace stored rendered text.
* No observable Agent answer, provider routing, tool selection, or Web UI
  behavior changes when comparing flag off versus flag on.

## 8. Non-goals and Deferred Work

This plan does not add a production artifact writer, migrate old traces, parse
financial prose, add providers, change loaders, expose raw payloads in Web UI,
or widen structured tracing beyond the first tool. Retention, encryption,
payload pruning, and Web/API ownership remain separate decisions.

## 9. Default-off Financial Provenance Runtime Integration (2026-07-13)

Implemented the financial-only runtime path behind
`VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE=1`:

```text
redacted financial result + existing tool arguments + optional execution metadata
  -> serializer
  -> provenance projector
  -> structured payload + existing metadata field
  -> TraceWriter
```

The LLM still receives the original legacy text. Flag-off does not call the
projector or add v1 trace fields. A serializer failure leaves a null structured
payload with `structured_payload_unavailable`; a projector failure preserves
the serializer payload and adds `financial_provenance_projection_failed`.

Complete provenance is only possible when the result or explicit execution
metadata contains it. The current primary Eastmoney envelope does not expose
all provider/upstream facts, so runtime behavior deliberately remains partial
rather than guessing.
