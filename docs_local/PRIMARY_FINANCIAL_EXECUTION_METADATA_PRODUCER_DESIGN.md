# Primary Financial Execution Metadata Producer Design

## 1. Purpose

Define a trustworthy producer for the per-call execution facts required by
the financial provenance projector. The producer must report what the
`FinancialStatementsTool` actually executed; it must not make the serializer,
AgentLoop, report builder, or an LLM infer a provider from a tool name, a
source label, or a payload shape.

Target flow:

```text
FinancialStatementsTool execution
  -> immutable per-call execution metadata
  -> runtime dual-write enrichment
  -> financial provenance projector
  -> structured trace
```

The legacy tool-result JSON string and the LLM context remain unchanged.

## 2. Current Execution Flow

```text
AgentLoop serial or parallel execution
  -> ToolRegistry.execute(name, params) -> str
  -> FinancialStatementsTool.execute(**kwargs) -> JSON string
      -> primary branch
          A/HK: _fetch_eastmoney_statement
          US: _fetch_sec_statement
      -> optional A-share fallback eligibility and Sina fetch
      -> JSON envelope / fallback audit envelope
  -> AgentLoop._finalize_tool_result
      -> legacy result to LLM context
      -> optional runtime dual-write trace enrichment
```

### Verified current facts

* The primary branch is selected in `FinancialStatementsTool.execute`: US uses
  SEC EDGAR; other supported markets use Eastmoney.
* `_fetch_eastmoney_statement` owns the Eastmoney F10 request, report-name
  mapping, and transport call. It returns rows or an error, not provenance.
* The tool's primary JSON envelope currently carries `source` (`eastmoney` or
  `sec_edgar`), `statement`, `period`, market, and rows. It does not carry a
  distinct `provider`, `upstream`, or execution metadata object.
* The fallback decision, A-share eligibility check, and fallback audit happen
  inside `FinancialStatementsTool.execute`. A normalized fallback result has
  explicit `provider=a_stock_data`, `source=sina_financial_report`, and an
  `upstream` supplied by the adapter when available.
* `_with_a_stock_fallback_audit` preserves the primary source, status, and
  error inside `fallback.primary` and `_data_quality` when fallback is used.
* `BaseTool.execute` and `ToolRegistry.execute` currently return only a
  string. The registry returns a JSON error string for registry-level errors.
* `ToolCallRequest` has no `execution_metadata` field. Current runtime code
  reads it defensively via `getattr`; fixture tests inject it with a test-only
  object. No production caller currently assigns it.

The metadata is therefore lost when `FinancialStatementsTool.execute` reduces
the execution branch to a legacy string and `ToolRegistry.execute` transports
only that string.

## 3. Execution Metadata Ownership

| Field | Source of truth | Producer | Allowed null | Missing behavior |
| --- | --- | --- | --- | --- |
| `provider` | Actual final successful branch | Financial tool execution layer | No for usable data | Empty plus `financial_provider_missing`; report remains partial. |
| `source` | Actual interface label emitted by the branch/adapter | Financial tool execution layer | No for usable data | Empty plus `financial_source_missing`; do not use provider as a substitute. |
| `upstream` | Explicit upstream platform fact owned by the branch/adapter | Provider adapter or financial tool branch mapping | Yes | `null` plus `financial_upstream_missing`; never guess it. |
| `fallback_used` | Primary/fallback branch decision | Financial tool orchestration | No once a branch ran | Unknown plus warning when execution cannot establish it. |
| `primary_error` | Primary failure that triggered fallback | Financial tool fallback orchestration | Yes | `null` after known primary success or when no safe error exists. |
| `statement_type` | Validated `statement` argument | Financial tool execution | No after validation | Warning; consumers must not classify rows. |
| `symbol` | Validated tool `code` argument | Financial tool execution | No after validation | Warning; consumers must not attach quality to a symbol. |
| `warnings` | Tool, provider, fallback, and redaction components | Producer aggregation | Yes | Empty list; never suppress a known warning. |

`row_count` and reporting periods are **not** producer-owned facts in v1.
They remain mechanical calculations by the normalizer/provenance projector
from structured rows. The producer may carry an explicit provider quality
object only when the executing branch already produced it; it must not create a
quality status from dates alone.

## 4. Producer Location Options

### Option A: FinancialStatementsTool produces execution metadata

The tool owns the primary branch and the fallback decision, so it can state
the actual final provider and preserve the primary error without inference.

Advantages:

* Closest to real primary/fallback control flow.
* Can distinguish final data provider from failed primary provider.
* Reuses existing fallback audit facts rather than reconstructing them later.

Risk:

* The current `execute` contract returns only a string and needs a compatible
  per-call wrapper.

### Option B: Provider/loader envelopes carry metadata

The Eastmoney/SEC/Sina adapters return a provider-specific result plus
provenance for the tool to aggregate.

Advantages:

* Provider facts sit nearest the request implementation.
* Potentially reusable for other tools.

Risks:

* Broadens loader/provider contracts and affects many callers.
* Is disproportionate for the financial-only MVP and conflicts with the
  current constraint not to refactor the provider chain.

### Option C: ToolRegistry infers provenance

The registry attempts to infer provider or fallback from a tool name, result
text, source string, or payload envelope.

This is not acceptable: it cannot observe the branch that actually ran and can
silently mislabel data.

### MVP recommendation

Use **Option A**, optionally consuming provider-owned facts where they already
exist. `FinancialStatementsTool` aggregates one immutable metadata object for
the call; ToolRegistry and AgentLoop transport it without interpretation.
Option B may later improve provider adapters, but it is not a prerequisite.
Option C is prohibited.

## 5. Compatible Return Contract

### Recommended: per-call `ToolExecutionResult` wrapper

Introduce a narrow internal result type, conceptually:

```python
ToolExecutionResult(
    legacy_result: str,
    execution_metadata: Mapping[str, Any] | None = None,
)
```

`FinancialStatementsTool` returns the wrapper only after the later runtime
implementation. `ToolRegistry.execute` accepts either the wrapper or an
existing string-returning tool result and normalizes legacy tools to the same
in-process representation with `execution_metadata=None`.

AgentLoop then:

1. passes `legacy_result` unchanged to guards, memory, and LLM context;
2. passes metadata as an explicit argument to `_finalize_tool_result`; and
3. gives the trace-only dual-write helper that metadata when the structured
   trace flag is enabled.

Do **not** mutate `ToolCallRequest` to add `execution_metadata`. Its current
shape originates with the LLM and it is the wrong lifetime for tool execution
facts.

### Rejected: tool-instance side channel

`tool.last_execution_metadata` or a module/global dictionary is unsafe: tool
instances may be reused and readonly tools run concurrently. It can associate
the wrong metadata with a different call.

### Rejected: mutable call-context side channel

Attaching metadata to `tc` after invocation risks hidden coupling and makes the
parallel path less explicit. A return wrapper bound to the call is clearer.

### Compatibility requirements

* `BaseTool.execute` may initially retain its documented string return type;
  the registry can widen its internal accepted type to `str | ToolExecutionResult`.
* Old tools remain string-returning with no metadata.
* A registry exception becomes a legacy JSON error plus no execution metadata.
* The wrapper is local runtime transport, not an LLM message, provider-chain
  type, or Web/API payload.
* The serial and parallel paths must pass the wrapper metadata explicitly.

## 6. Canonical Execution Metadata v1

```json
{
  "schema_version": "financial_execution_metadata.v1",
  "tool_name": "get_financial_statements",
  "symbol": "300750.SZ",
  "statement_type": "income",
  "provider": "eastmoney",
  "source": "eastmoney",
  "upstream": "eastmoney",
  "fallback": {
    "used": false,
    "primary_provider": "eastmoney",
    "primary_error": null
  },
  "execution_quality": {
    "provider_success": true,
    "warnings": []
  },
  "warnings": []
}
```

The names above reflect current code facts: primary source is presently the
tool-owned label `eastmoney`, not an existing `eastmoney_financial_report`
constant. A future stable dataset label must be introduced explicitly at the
tool/provider branch; it must not be retroactively inferred by a consumer.

Ownership is intentionally split:

| Fact | Owner |
| --- | --- |
| Final provider/source/upstream, fallback branch, primary error, symbol, statement type | Financial tool execution producer |
| Existing provider/adapter warnings | Financial tool execution producer preserves them |
| Rows, row count, reporting periods, latest period | Structured payload plus normalizer/projector mechanical calculation |
| Schema completeness and financial confidence | FinancialConfidenceExtractor |

`upstream` is the external platform actually queried or explicitly declared
by the adapter, not a synonym for `provider`. For current Eastmoney and SEC
paths, any mapping must be maintained beside the branch code as an explicit
execution fact. Where no adapter fact is available, it is `null` and warned.

## 7. Primary and Fallback Behavior

### Primary success

* Final `provider`, `source`, and explicit `upstream` describe the successful
  primary branch.
* `fallback.used=false`; `primary_error=null`.
* The structured payload remains the existing legacy JSON envelope; no rows,
  dates, or quality status are manufactured by metadata.

### Primary failure plus fallback success

* Final `provider`, `source`, and `upstream` identify the fallback result.
* `fallback.used=true`.
* `fallback.primary_provider` identifies the attempted primary only when the
  execution branch knows it.
* The preserved primary error is redacted and bounded.
* The failed primary must never be presented as the provider of returned data.

### All branches fail

* Preserve the existing legacy error result.
* Metadata may record attempted branches and safe, redacted errors.
* No structured financial data is claimed; downstream schema stays missing or
  failed rather than complete.

## 8. Error and Redaction Policy

Execution metadata must never include API keys, cookies, authorization headers,
environment values, secret-bearing URLs, raw response bodies, stack traces, or
LLM reasoning. `primary_error` must be produced by a shared safe-error helper
that redacts known secrets, limits length, and preserves a compact category or
message suitable for audit. If a safe error cannot be produced, use `null` and
append a machine warning instead.

## 9. Concurrency and Lifecycle

AgentLoop has two execution paths:

* `_execute_single` invokes and finalizes one tool call.
* `_execute_parallel` executes readonly tools in worker threads, then
  finalizes ordered results on the main path.

Metadata must travel in the result returned for the specific `call_id`:

```text
(tool_call, ToolExecutionResult, elapsed_ms)
  -> _finalize_tool_result(..., execution_metadata=...)
```

The parallel worker must return its own wrapper; the ordered finalizer must
retain the original `tc.id`. Guard-generated results and timeout/registry
errors have no producer metadata unless they explicitly create safe error
metadata. No global state, module state, thread-local cache, or reusable-tool
`last_execution_metadata` field is allowed.

## 10. Feature Flag Relationship

`VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE` stays default off. The producer
may create compact, in-process metadata alongside the tool return regardless
of the trace flag, because it records execution facts rather than changing
provider behavior. Only when the flag is `1` may AgentLoop serialize it into
structured trace enrichment.

The flag must not change primary/fallback selection, requests, returned legacy
text, guards, Agent output, or Web UI behavior. Flag-off trace events keep the
legacy shape.

## 11. Migration Plan

1. Fixture-first `ToolExecutionResult` and registry normalization contract.
2. Serial AgentLoop transport proof with a string-returning legacy tool.
3. Parallel readonly transport proof with distinct metadata per call.
4. FinancialStatementsTool primary producer for its existing source labels.
5. A-share fallback producer preserving final and primary provenance.
6. Runtime projector integration using explicit return metadata, not `tc`
   mutation.
7. One controlled real run with structured trace enabled and shell tools off.
8. Read-only artifact completeness observation.

Every step is default-off, fixture-tested, and independently reversible.

## 12. Next Implementation Acceptance Criteria

1. Existing string-returning tools are unchanged.
2. FinancialStatementsTool legacy JSON is byte-for-byte unchanged.
3. Primary metadata is explicit for income, balance, and cashflow fixtures.
4. Fallback metadata identifies the final fallback and preserves a safe
   primary error.
5. Serial and parallel paths retain per-call metadata and `call_id` identity.
6. A registry exception, timeout, or serializer failure cannot block legacy
   tool behavior.
7. No mutable shared execution metadata exists.
8. Flag-off trace shape remains unchanged.
9. Complete explicit fixtures produce a complete artifact; absent facts remain
   partial with warnings.
10. No implementation derives provider/upstream from tool name, payload shape,
    source text, or a configured default.

## 13. Non-goals

This design does not implement a producer, run a real Agent task, add market
metadata, modify loaders/providers/TraceWriter, generate production artifacts,
change Web UI, add a database, implement valuation, or migrate all tools.

## 14. Fixture-first Transport Proof Status (2026-07-13)

The generic transport proof is implemented without modifying
`FinancialStatementsTool`:

* `ToolExecutionResult` is an immutable per-call wrapper for legacy text,
  optional metadata, and internal transport warnings.
* `ToolRegistry.execute(...)` remains the legacy string interface; additive
  `execute_with_metadata(...)` normalizes old string tools and future wrapper
  tools.
* AgentLoop uses the additive interface in both serial and parallel paths,
  passes metadata explicitly to finalization, and keeps it out of LLM context.
* A deep copy plus immutable container normalization prevents later mutation of
  caller metadata from affecting the completed call.
* Fixture tests cover legacy compatibility, serial and parallel `call_id`
  association, registry errors, invalid metadata, trace flag behavior, and the
  financial provenance boundary.

The next task remains the actual primary/fallback producer inside the financial
tool. No provider fact is created by this generic transport layer.
