# Structured Tool Result Trace Contract

## 1. Purpose

Define a versioned trace contract that preserves two distinct representations
of every tool result:

* `structured_payload` is the machine-readable, redacted result used by report
  builders, confidence extraction, audit, exports, and future Web UI views.
* `human_summary` is the bounded, redacted text supplied to the LLM context and
  readable in ordinary run history.

The contract addresses a confirmed compatibility gap: historical traces can
record `get_financial_statements` output as rendered text. A post-processor can
then see that the tool was called, but cannot safely reconstruct income,
balance, cashflow, provider, period, or fallback facts. It must generate a
partial artifact rather than infer them.

This document is design only. It does not change AgentLoop, tool
implementations, providers, loaders, Web UI, or existing traces.

## 2. Current Findings

### Current trace events

`TraceWriter` appends JSONL records. It adds `ts` and can offload large text
fields to safe sidecar files.

| Event | Current structured fields | Current result representation |
| --- | --- | --- |
| `tool_call` | `type`, `iter`, `tool`, `call_id`, redacted `args`, `ts` | No result yet |
| `tool_result` | `type`, `iter`, `tool`, `call_id`, `status`, `elapsed_ms`, `preview`, `ts` | `result` is one redacted string, inline or a text sidecar |
| `answer` | `type`, `iter`, `content` or a text sidecar, `ts` | Human-facing final text |

The current registry/tool interface returns `str`. In AgentLoop,
`_finalize_tool_result(...)` redacts that string, adds the same string to LLM
context, and passes it to `TraceWriter.write_tool_result(...)`. This preserves
text and offload support, but it does not distinguish a JSON tool envelope from
rendered prose.

### Why financial confidence cannot be recovered

`trace_collector` can parse a `result` string only when it is a JSON object. A
rendered financial result is not a safe source for field reconstruction. The
collector therefore records missing income, balance, and cashflow facts, and
the artifact generator correctly emits `partial` rather than guessing values.

## 3. Tool Result Contract v1

New producers should add `trace_schema_version: "tool_result.v1"` while
retaining legacy fields for existing readers.

### 3.1 `tool_call`

```json
{
  "type": "tool_call",
  "trace_schema_version": "tool_result.v1",
  "ts": 0,
  "iter": 1,
  "tool_name": "get_financial_statements",
  "call_id": "call_123",
  "args": {"code": "300750.SZ", "statement": "income"}
}
```

`args` must be redacted before persistence. The existing `tool` field may be
kept as an alias during migration.

### 3.2 `tool_result`

```json
{
  "type": "tool_result",
  "trace_schema_version": "tool_result.v1",
  "ts": 0,
  "iter": 1,
  "tool_name": "get_financial_statements",
  "call_id": "call_123",
  "args": {"code": "300750.SZ", "statement": "income"},
  "status": "ok",
  "elapsed_ms": 412,
  "structured_payload": {"ok": true, "data": {}},
  "human_summary": "Income statement retrieved for 300750.SZ.",
  "metadata": {
    "provider": "a_stock_data",
    "source": "sina_financial_report",
    "upstream": "sina",
    "data_quality": {},
    "timestamps": {"observed_at": "2026-07-13T00:00:00Z"},
    "payload_status": "structured"
  }
}
```

Required fields are `tool_name`, `args`, `status`, `structured_payload`,
`human_summary`, and `metadata`. `structured_payload` may be `null` only when
`metadata.payload_status` explains why, for example `unstructured_legacy_tool`
or `redacted_unavailable`.

Large payloads may be written as a JSON sidecar using
`structured_payload_path`, plus SHA-256 and byte count metadata. The resolver
must validate that the sidecar stays inside the trace directory, as current
text-sidecar resolution already does. `human_summary` remains bounded text and
may use the existing text-offload mechanism.

### 3.3 `final_answer`

```json
{
  "type": "answer",
  "trace_schema_version": "tool_result.v1",
  "ts": 0,
  "iter": 2,
  "content": "Human-facing research response.",
  "metadata": {"content_status": "available"}
}
```

The final answer is interpretation, never a replacement for structured
financial, market, source, or date fields.

## 4. Field Ownership and Metadata Rules

`structured_payload` is the canonical, redacted tool envelope. It must retain
tool-originated `ok`, `data`, errors, symbol, statement type, and source facts.
`metadata` duplicates only high-value indexing/audit fields; it must not become
a second independently maintained data model.

For financial statements, the producer or a mechanical extractor must expose:

* `provider`, `source`, `upstream`, and fallback/primary-error information;
* `statement_type`, requested symbol, reporting period/latest data date, and
  row count when known;
* `_data_quality` or an equivalent data-quality object;
* warnings without suppressing provider failure or fallback usage.

LLM-generated text must never populate price, statement values, provider,
source, upstream, reporting period, or data-quality metadata.

## 5. Safety and Privacy

Redaction happens before both `structured_payload` and `human_summary` are
persisted. Producers must recursively redact secret-like argument and result
fields. A trace must not contain API keys, authorization headers, cookies,
OAuth files, environment values, or local absolute paths outside approved
artifact references. Binary/raw private documents should be represented by a
safe reference and availability metadata, not copied into payloads.

`status` is one of `ok`, `error`, `blocked`, `skipped`, or `cancelled`. Errors
must retain a safe machine code and human summary, without exposing secrets.

## 6. Migration Strategy

### Legacy traces

Existing traces remain immutable. Readers use this precedence order:

1. Resolve and consume `structured_payload` or its validated JSON sidecar.
2. For legacy entries, parse `result` only when it is a complete JSON object.
3. Otherwise classify the payload as unavailable/unstructured, add a structured
   warning, and generate a partial schema/artifact.

Readers must not regex-parse rendered financial prose to manufacture rows,
dates, or provenance. Historical text is evidence for a human, not a verified
machine contract.

### Dual-write rollout

1. Add a pure serializer/extractor with fixture tests for JSON, text, errors,
   redaction, and JSON sidecar resolution.
2. Add `structured_payload` alongside existing `result`; retain `tool`,
   `preview`, and `result` for current CLI/API/history consumers.
3. Enable only for selected read-only, JSON-envelope tools, beginning with
   `get_market_data` and `get_financial_statements`.
4. Run controlled trace-to-artifact observation and compare legacy versus v1
   collector coverage.
5. Expand only after provenance, period, fallback, and data-quality fields are
   demonstrably recoverable. Do not remove legacy text fields in v1.

The migration should be feature-flagged during observation, default off until
the controlled real-run result is accepted. The exact flag name and ownership
are implementation decisions for a later task.

## 7. Consumer Behavior

`trace_collector` should prefer `structured_payload`, then use legacy JSON
result parsing as a compatibility fallback. `report_builder` and
`FinancialConfidenceExtractor` remain consumers: they assemble schema and
confidence from verified facts, rather than parsing prose. `artifact_generator`
records `complete`, `partial`, or `failed` based on the resulting schema.

Future Web UI reads `research_schema.json`, not raw trace payloads. Trace data
remains execution/audit evidence and should not require browser-side parsing.

## 8. Acceptance Criteria for a Future Implementation

* A controlled `get_financial_statements` trace preserves income, balance, and
  cashflow as structured payloads with provider, source, upstream, reporting
  period, data quality, fallback state, and warnings.
* Offloaded JSON payloads resolve safely and produce the same collector result
  as inline payloads.
* Legacy text-only traces produce explicit compatibility warnings and partial
  artifacts, never inferred financial facts.
* Redaction tests show no secret-like fields in inline or sidecar payloads.
* Existing LLM tool-context text, trace history, provider chain, and loader
  behavior remain compatible during the dual-write period.

## 9. Deferred Decisions

* A production feature flag name and default.
* Payload retention, encryption, and pruning policy.
* Whether non-JSON tools receive a tool-specific structured adapter.
* Production post-run artifact writing and API/Web UI ownership.
