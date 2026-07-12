# Agent-to-Schema Pipeline Design

## 1. Purpose

This document designs how a completed Agent research run can be converted into
a Structured Research Report Schema artifact.

Current proven path:

```text
FinancialStatementsTool().execute(...)
    -> controlled fallback-shaped financial output
    -> build_research_report(...)
    -> Structured Research Report Schema
```

Next target path:

```text
AgentLoop research run
    -> tool results collection
    -> schema producer
    -> Structured Research Report artifact
```

This is design only. It does not modify AgentLoop, tools, provider chains, Web
UI, or live data behavior.

## 2. Current State

Already available:

* `FinancialStatementsTool`.
* `agent/src/reports/report_builder.py`.
* `build_research_report(...)`.
* Direct Tool Output -> Research Report Schema proof.
* AgentLoop run directories under `agent/runs`.
* Agent/session traces written by `TraceWriter`.
* Tool results recorded as `tool_result` events in `trace.jsonl`.
* Final answers recorded as `answer` events in trace.
* Runtime output directories such as `agent/runs`, `agent/sessions`, and
  `local_reports` are ignored by Git.

Relevant current files:

```text
agent/src/agent/loop.py
agent/src/agent/trace.py
agent/src/reports/report_builder.py
scripts/observe_direct_tool_schema_pipeline.py
agent/tests/test_direct_tool_schema_pipeline.py
docs_local/REPORT_SCHEMA_AND_AGENT_WORKFLOW_DESIGN.md
docs_local/MINIMAL_SCHEMA_PRODUCING_PROOF_DESIGN.md
```

Important observed behavior:

* AgentLoop writes `tool_call` events before tool execution.
* AgentLoop writes `tool_result` events after execution.
* Large tool results can be stored in sidecar files and resolved later through
  `TraceWriter.read(..., resolve_offloads=True)`.
* AgentLoop already captures `_data_quality` internally for report summaries,
  but the schema producer should not depend on private in-memory state for the
  MVP.

## 3. Pipeline Placement Options

## Option A: Inside AgentLoop

Description:

AgentLoop updates schema state during each tool call.

Pros:

* Real-time schema state.
* Schema is tightly linked to the active run.
* Future UI could stream structured partial progress.

Cons:

* Highly invasive to AgentLoop.
* Higher regression risk.
* Harder to roll back.
* Could affect existing tool execution, tracing, and final-answer behavior.
* Adds product schema responsibility to the core reasoning loop.

Assessment:

Not recommended for MVP.

## Option B: Post-Processor After Run

Description:

AgentLoop remains unchanged. After a run completes, a post-processor reads
trace artifacts, extracts tool calls/results and final answer, then calls the
schema producer.

Pros:

* Low risk.
* Does not affect Agent reasoning.
* Does not change tool execution.
* Easy to test with fixture traces.
* Easy to roll back.
* Fits current `TraceWriter` artifact model.

Cons:

* Not real-time.
* Depends on trace completeness.
* Needs robust parsing of offloaded tool results.
* Needs clear behavior when traces are partial or corrupted.

Assessment:

Recommended for MVP.

## Option C: Hybrid

Description:

AgentLoop records standardized tool events. A post-processor uses those events
to build schema.

Pros:

* Better long-term architecture.
* Keeps schema generation outside AgentLoop.
* Can support streaming or near-real-time schema later.
* Creates a stable tool event contract.

Cons:

* Requires defining and implementing a tool event contract.
* More work than Option B.
* Still requires trace/post-processing logic.

Assessment:

Recommended later evolution after Option B proves useful.

## 4. Recommended Placement

MVP recommendation:

```text
Option B: Post-Processor After Run
```

Evolution path:

```text
Option B now
    -> fixture trace proof
    -> controlled run trace proof
    -> Option C standardized tool event contract
```

Reason:

The project already has working AgentLoop tracing. Reading existing artifacts is
much safer than changing the core reasoning loop before the schema product
contract stabilizes.

## 5. Tool Result Collection Contract

The schema producer should receive a normalized run collection object.

Minimal format:

```json
{
  "run_id": "",
  "symbol": "",
  "tool_results": [
    {
      "tool_name": "",
      "args": {},
      "result": {},
      "status": "",
      "timestamp": ""
    }
  ],
  "final_answer": ""
}
```

Recommended additional fields:

```json
{
  "trace_dir": "",
  "generated_at": "",
  "collection_warnings": [],
  "raw_event_count": 0
}
```

Collection source for MVP:

* `trace.jsonl` in a run/session directory.
* `tool_call` events provide tool name, call id, and arguments.
* `tool_result` events provide status and result payload or result sidecar.
* `answer` event provides final answer text.

## 6. Required Tool Results

## `market_snapshot`

Tool:

```text
get_market_data
```

Required fields:

* symbol
* price/close/latest value when available
* date or timestamp
* `_data_quality`
* provider/source if available
* warnings/errors if available

## `financial_health`

Tools:

```text
get_financial_statements income
get_financial_statements balance
get_financial_statements cashflow
```

Required fields:

* statement type
* provider
* source
* upstream
* period
* latest data date / reporting period
* metrics or raw rows
* `_data_quality`
* warnings/errors
* fallback status

## `data_confidence`

Sources:

* `_data_quality`
* provider/source fields
* tool result status
* warnings
* errors
* fallback metadata

## `investment_memo`

Source:

* Agent final answer or later LLM interpretation step.

Boundary:

The final answer may fill narrative placeholders, but must not overwrite facts
from tool results.

## 7. Schema Producer Responsibility

Program must fill:

* symbol
* market
* asset type
* provider
* source
* price
* financial numbers
* report date / reporting period
* data quality
* warnings
* limitations

Agent / LLM may fill:

* thesis
* bull case
* bear case
* key risks
* monitor items

LLM must not fill:

* price
* revenue
* net profit
* cash flow
* provider
* source
* dates
* fallback status
* target price
* analyst forecast

## 8. Partial Schema Policy

## Market Data Missing

Behavior:

```text
market_snapshot.status = "missing"
data_confidence.warnings += ["market_data_missing"]
```

Policy:

* Do not generate price-related conclusions.
* Preserve other available sections.

## Market Data Partial / Unknown

Behavior:

```text
market_snapshot.status = "partial" or "unknown"
data_confidence.warnings += relevant warning
```

Policy:

* Interpretation may discuss only available facts.
* Strong time-sensitive claims should be blocked or downgraded.

## Financial Data Partial

Behavior:

```text
financial_health.status = "partial"
financial_health.quality.warnings += ["income_statement_missing", ...]
```

Policy:

* Allow limited financial interpretation using available statements.
* Explicitly name missing statements.

## All Financial Data Missing

Behavior:

```text
financial_health.status = "missing"
financial_health.statements = []
```

Policy:

* Do not generate financial conclusions.
* Data confidence must show the failure.

## Agent Final Answer Missing

Behavior:

```text
investment_memo.thesis = ""
investment_memo.bull_case = []
investment_memo.bear_case = []
investment_memo.key_risks = []
investment_memo.monitor_items = []
```

Policy:

* Schema can still be generated.
* Facts remain usable.
* UI should show memo as missing or pending.

## Invalid Symbol

Behavior:

* Schema generation should reject the run or return a blocked schema.
* Do not guess the symbol in the schema producer.

## 9. Artifact Policy

MVP output location options:

```text
local_reports/research_schema_<run_id>.json
```

or:

```text
agent/runs/<run_id>/artifacts/research_schema.json
```

Recommendation:

Use run artifact directory for Agent-run outputs:

```text
agent/runs/<run_id>/artifacts/research_schema.json
```

Use `local_reports` for one-off scripts and experiments:

```text
local_reports/research_schema_<run_id>.json
```

Requirements:

* Generated schema artifacts must not be committed.
* Artifact must contain `research_meta.run_id`.
* Artifact must contain `research_meta.generated_at`.
* Artifact should be readable by future API/Web UI.
* Persistence/database storage should be deferred.

## 10. Testing Strategy

Next implementation tests should cover:

1. Fixture run trace -> schema success.
2. Missing market data -> partial schema.
3. Missing financial data -> warning.
4. Fallback financial data -> `data_confidence` includes fallback warning.
5. Agent final answer missing -> schema still generated.
6. Invalid symbol -> schema rejected.

Test constraints:

* No live data.
* No Web UI.
* No AgentLoop live run.
* No `.env` reads.

Recommended first implementation:

```text
scripts/observe_agent_trace_schema_pipeline.py
```

using fixture trace JSONL and sidecar-free tool results.

## 11. MVP Acceptance Criteria

Input:

```text
controlled run trace fixture
```

Output:

```text
Structured Research Report Schema
```

Must contain:

* `research_meta.run_id`
* `symbol.normalized_symbol`
* `financial_health`
* `data_confidence`
* `limitations`

Must guarantee:

* provider/source/date are not generated by the LLM
* warnings are preserved
* partial data does not crash schema generation
* schema can be consumed by Web UI later

## 12. Non-goals

This phase does not do:

* Web UI.
* Database persistence.
* Portfolio dashboard.
* Multi-stock batch.
* Valuation engine.
* Metrics engine.
* Trading recommendation.
* Target price.
* Live Agent run.
* Live data fetching.
* AgentLoop refactor.

## 13. Open Questions

1. Should the first post-processor read `trace.jsonl` directly or consume a
   pre-normalized trace fixture?
2. Should post-processing happen automatically after every run or only on
   explicit CLI/API request?
3. Should final answer text be parsed into memo fields, or should the memo
   remain placeholder until a structured interpretation step exists?
4. Should schema artifacts live under `agent/runs` by default or always under
   `local_reports` for early proofs?
5. Should schema validation later use Pydantic or plain dict validation?

## 14. Recommended Next Step

Next task:

```text
Agent Trace Fixture -> Schema Proof
```

Scope:

* fixture trace only
* no live AgentLoop run
* no Web UI
* no live data

Goal:

Prove that existing trace-style `tool_call`, `tool_result`, and `answer` events
can be collected into the run collection contract and then passed into the
schema producer.
