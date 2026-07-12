# Controlled Real Run Schema Artifact Design

## 1. Purpose

This document designs how a completed real Agent run can be converted into a
structured `research_schema.json` artifact through a post-processor.

Target path:

```text
controlled real Agent run
  -> existing run/session trace artifacts
  -> schema post-processor
  -> research_schema.json
  -> future Research Workspace / API / export
```

This round is design only. It does not modify AgentLoop, Web UI, provider
chain, loader, or runtime behavior.

## 2. Current Run Artifact Findings

## AgentLoop entry

Observed files:

```text
agent/src/agent/loop.py
agent/src/agent/trace.py
agent/src/session/service.py
agent/src/session/store.py
agent/api_server.py
agent/src/ui_services.py
```

`AgentLoop.run(...)` creates or reuses a run directory under:

```text
agent/runs/<run_id>
```

The run directory is created by `RunStateStore.create_run_dir(...)`. The user
request is saved there through `RunStateStore.save_request(...)`.

When the run is associated with a Web/API session, AgentLoop writes trace
events to:

```text
agent/sessions/<session_id>/trace.jsonl
```

When there is no session id, AgentLoop writes trace events to:

```text
agent/runs/<run_id>/trace.jsonl
```

## Session artifacts

`SessionStore` persists session data under:

```text
agent/sessions/<session_id>/
  session.json
  messages.jsonl
  attempts/<attempt_id>/attempt.json
```

`Attempt` records include:

```text
attempt_id
session_id
status
prompt
run_dir
summary
metrics
```

`SessionService` stores `attempt.run_dir = result.get("run_dir")` after the
Agent run completes. It also writes an assistant message whose metadata includes:

```json
{
  "run_id": "<run_dir basename>",
  "status": "completed"
}
```

This means a Web session can link from `session_id + attempt_id` to the
physical run directory, but the trace itself is currently session-scoped.

## Trace format

`TraceWriter` writes one JSON object per line to:

```text
trace.jsonl
```

Relevant event types already available:

```text
start
message
tool_call
tool_result
answer
end
```

Tool call events include:

```json
{
  "type": "tool_call",
  "iter": 1,
  "tool": "get_market_data",
  "call_id": "...",
  "args": {}
}
```

Tool result events include:

```json
{
  "type": "tool_result",
  "iter": 1,
  "tool": "get_market_data",
  "call_id": "...",
  "status": "ok",
  "elapsed_ms": 123,
  "preview": "...",
  "result": "{...}"
}
```

Large result fields may be offloaded to sidecar files under the trace
directory, for example:

```text
tool-results/<hash>.txt
trace-blobs/<hash>.txt
```

`TraceWriter.read(..., resolve_offloads=True)` can safely resolve sidecar
payloads back into trace entries.

Final answers are recorded as:

```json
{
  "type": "answer",
  "iter": 3,
  "content": "..."
}
```

Long answer content may also be offloaded and resolved through
`TraceWriter.read(..., resolve_offloads=True, resolve_fields={"content"})`.

## Current Web/API access

Backtest-style run details are exposed through:

```text
GET /runs
GET /runs/{run_id}
```

These endpoints read `agent/runs/<run_id>` and build a `RunResponse`. They are
currently oriented around backtest/run artifacts such as metrics, artifacts,
price series, logs, and run context.

Web chat sessions use:

```text
POST /sessions
POST /sessions/{session_id}/messages
GET /sessions/{session_id}/messages
GET /sessions/{session_id}/events
```

The Agent page reads session messages and listens to SSE events. On completion,
it can derive `run_id` from `run_dir` in the `attempt.completed` event or from
assistant message metadata.

## Current limitations

* There is no existing `research_schema.json` artifact.
* There is no current API endpoint for `research_schema.json`.
* Web session traces are written under `agent/sessions/<session_id>`, while
  persistent run artifacts live under `agent/runs/<run_id>`.
* The current trace collector handles loaded event objects, but not yet reading
  a real trace directory.
* `build_research_report(...)` currently requires an explicit `input_symbol`.
  A real post-processor must derive this from the user prompt, tool args, or a
  safe caller-provided symbol.
* The existing `/runs/{run_id}` response is backtest-centric and should not be
  overloaded until the schema artifact is stable.

## 3. Recommended MVP Architecture

Recommended MVP:

```text
AgentLoop run completes
  -> no AgentLoop mutation
  -> post-processor locates trace directory
  -> TraceWriter.read(resolve_offloads=True)
  -> trace_collector
  -> build_research_report(...)
  -> write research_schema.json
```

The post-processor should be a separate helper, not an AgentLoop inline step.

Recommended initial helper shape:

```text
build_research_schema_artifact(
  run_id,
  session_id=None,
  attempt_id=None,
  input_symbol=None,
  output_path=None
)
```

For the first controlled proof, `input_symbol` should be explicit, for example:

```text
600519.SH
```

Reason:

Symbol inference from natural language or tool calls is a product decision. The
first real trace proof should validate artifact production, not symbol
inference.

## 4. Trace Location Resolution

The post-processor should resolve traces in this order:

1. If `session_id` is provided:

```text
agent/sessions/<session_id>/trace.jsonl
```

2. If no session trace exists and `run_id` is provided:

```text
agent/runs/<run_id>/trace.jsonl
```

3. If both `session_id` and `run_id` are provided and both traces exist:

Prefer the session trace for Web/API session runs, because AgentLoop writes to
the session trace when `session_id` is present.

The project already has:

```text
TraceWriter.find_trace_dir(run_id, runs_dir=None, sessions_dir=None)
```

However, this helper accepts one id and checks `sessions/<id>` then
`runs/<id>`. For Web session usage, the caller must pass `session_id`, not
`run_id`, if it wants the session trace.

## 5. Artifact Location Policy

Recommended production artifact location:

```text
agent/runs/<run_id>/artifacts/research_schema.json
```

Reason:

* `agent/runs/<run_id>` is the stable run artifact root.
* `/runs/{run_id}` already reads artifacts from the run directory.
* Future Web UI and export flows can find one artifact by run id.

Recommended optional debug copy:

```text
agent/sessions/<session_id>/attempts/<attempt_id>/research_schema.json
```

This is not recommended for MVP unless needed for session debugging.

One-off local proof output, if needed:

```text
local_reports/research_schema_<run_id>.json
```

`local_reports` must remain Git-ignored and should not be used as the product
artifact path.

## 6. Minimal Real-Run Post-Processor Contract

Input:

```json
{
  "run_id": "",
  "session_id": "",
  "attempt_id": "",
  "input_symbol": "600519.SH",
  "trace_dir": "",
  "output_path": ""
}
```

Output:

```json
{
  "ok": true,
  "run_id": "",
  "session_id": "",
  "attempt_id": "",
  "trace_dir": "",
  "schema_path": "",
  "warnings": []
}
```

Failure output:

```json
{
  "ok": false,
  "error": "",
  "warnings": []
}
```

Required behavior:

* Never run AgentLoop.
* Never call providers.
* Never call live data.
* Never read `.env`.
* Read only trace artifacts and sidecars under the selected trace directory.
* Resolve offloaded `result` and `content` fields safely.
* Preserve data-quality warnings in the schema.
* Fail closed on invalid or ambiguous symbols.

## 7. Required Trace Fields

Already sufficient for the current collector:

* `tool_result.type`
* `tool_result.tool`
* `tool_result.status`
* `tool_result.result`
* `answer.content`

Useful but not currently required:

* `tool_result.call_id`
* `tool_result.elapsed_ms`
* `tool_call.args`
* `start.prompt`
* `end.status`

Potential minimal future additions:

* Add `run_id` and `session_id` to trace start/end events.
* Add `attempt_id` to trace start/end events for Web session runs.
* Add a stable `event_schema_version`.

These are not required for the first real-run proof if the post-processor is
called with `run_id/session_id/attempt_id` from the outside.

## 8. Symbol Handling Policy

MVP controlled proof:

```text
input_symbol must be provided explicitly by the caller.
```

Do not infer symbol from:

* final answer markdown
* user prompt text
* first random tool result

Later evolution:

* If only one unique stock symbol appears across guarded stock tool calls, the
  post-processor may propose it as `candidate_symbol`.
* If multiple symbols appear, produce a multi-symbol unsupported warning.
* If the symbol needs confirmation, fail closed.

## 9. Partial Schema Policy

If market data is absent:

```text
market_snapshot.status = missing
data_confidence.warnings includes market_data_missing
```

If financial data is absent:

```text
financial_health.status = missing
data_confidence.warnings includes financial_data_missing
```

If only one or two financial statements are present:

```text
financial_health.status = partial
missing statements are listed as warnings
```

If final answer is absent:

```text
investment_memo remains empty/placeholder
facts still generate
```

If trace is missing or unreadable:

```text
post-processor returns ok=false
no research_schema.json is written
```

If symbol is invalid, ambiguous, or requires confirmation:

```text
post-processor returns ok=false
no research_schema.json is written
```

## 10. API and Web UI Integration Later

Not part of MVP proof.

Future API options:

## Option A: Extend `/runs/{run_id}`

Add optional `research_schema` field when:

```text
agent/runs/<run_id>/artifacts/research_schema.json
```

exists.

Pros:

* Reuses existing run-detail endpoint.
* Simple for Web UI.

Cons:

* `/runs/{run_id}` is currently backtest-oriented.
* Could make response payload large.

## Option B: Add `/runs/{run_id}/research-schema`

Pros:

* Clear artifact-specific endpoint.
* Keeps existing run response stable.

Cons:

* Requires new endpoint.

Recommended later choice:

```text
Option B: GET /runs/{run_id}/research-schema
```

The first implementation should not happen until the artifact proof passes.

## 11. Controlled Real-Run Proof Plan

Recommended next proof:

1. User manually runs or selects one already-completed controlled Agent session.
2. Capture:
   * `session_id`
   * `attempt_id`
   * `run_id`
   * explicit `input_symbol`
3. Run a post-processor script manually:

```bash
.venv/bin/python scripts/observe_real_run_trace_to_schema.py \
  --session-id <session_id> \
  --run-id <run_id> \
  --symbol 600519.SH \
  --output-dir local_reports
```

4. The script reads:

```text
agent/sessions/<session_id>/trace.jsonl
```

5. The script emits only a compact console summary.
6. Optional JSON output goes to ignored `local_reports`.
7. No Web UI or API integration is changed.

This proof should still be observation-only. The first script should not write
to `agent/runs/<run_id>/artifacts/research_schema.json` unless explicitly
approved.

## 12. Acceptance Criteria

Controlled real-run observation passes if:

* The post-processor finds a trace directory.
* `TraceWriter.read(..., resolve_offloads=True)` returns events.
* At least one relevant `tool_result` is collected.
* `build_research_report(...)` returns a valid schema.
* Schema contains:
  * `research_meta`
  * `symbol`
  * `market_snapshot`
  * `financial_health`
  * `investment_memo`
  * `valuation`
  * `risks`
  * `data_confidence`
  * `limitations`
* Provider/source/date fields come from tool results.
* Warnings are preserved.
* No provider or live data call occurs during post-processing.

Failure is acceptable and useful if the result clearly explains:

* trace missing
* tool results missing
* symbol ambiguous
* final answer missing
* tool output shape incompatible

## 13. Non-goals

This design does not include:

* AgentLoop modification.
* Web UI modification.
* New provider integration.
* Loader changes.
* Live data calls.
* Automatic schema generation after every run.
* Database persistence.
* Multi-symbol report schema.
* Valuation engine.
* Financial metrics engine.
* Trading or portfolio workflow.

## 14. Recommended Next Step

Next recommended task:

```text
Controlled Real Run Trace Observation Script
```

Boundary for that task:

* Script only.
* Read existing trace artifacts.
* Do not run AgentLoop.
* Do not run Web UI.
* Do not call live data.
* Write optional output only to ignored `local_reports`.
* Do not write production `research_schema.json` until one observation passes.

## 15. Historical Trace Observation Result

Date: 2026-07-12

Observation target:

```text
agent/runs/20260705_170559_16_fc55fe/trace.jsonl
```

Invocation:

```bash
.venv/bin/python scripts/observe_real_trace_to_schema.py \
  --run-id 20260705_170559_16_fc55fe \
  --symbol 300750.SZ \
  --output-dir local_reports
```

Result summary:

* The script successfully read the historical run trace.
* `TraceWriter.read(..., resolve_offloads=True)` successfully handled the trace.
* The trace contained 53 events and 19 tool results.
* Tool results included `get_market_data`, `get_financial_statements`,
  `get_stock_news`, `get_research_reports`, `get_sector_info`, and related
  stock tools.
* The trace contained a final answer.
* `trace_collector` and `build_research_report(...)` generated a structured
  schema summary.

Important gap:

* The historical financial statement result only exposed `indicators`.
* It did not contain income, balance, or cashflow statement outputs.
* Therefore the proof confirms real trace readability and schema construction,
  but it does not prove a complete financial-statement schema from this specific
  historical run.

Compatibility result:

```text
can_read_trace: true
has_tool_results: true
has_required_financial_results: false
can_build_schema: true
suitable_for_future_artifact: true
```

Conclusion:

The current post-processing design is viable for a first read-only real-trace
schema artifact workflow. Before writing production
`agent/runs/<run_id>/artifacts/research_schema.json`, run the observation
against a trace that includes income, balance, and cashflow tool results.
