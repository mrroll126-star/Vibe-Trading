# Research Schema Artifact Design

## 1. Purpose

A research_schema.json artifact is the stable, structured representation of a
completed research run. It lets the future Research Workspace, exports, and
history views consume one auditable report object instead of parsing Agent
Markdown or replaying a trace.

```text
trace.jsonl: immutable execution evidence
research_schema.json: derived, versioned product read model
```

The artifact does not replace the trace. The trace remains the audit source for
tool calls, tool results, timing, and raw run events. The artifact is a
deterministic, schema-versioned summary built from those events and must retain
the run identifier needed to trace it back.

This document is design only. It does not generate artifacts or change runtime
behavior.

## 2. Artifact Lifecycle

Recommended MVP lifecycle:

```text
Agent run completes
  -> existing trace.jsonl and run metadata
  -> post-processor reads trace with offloads resolved
  -> trace_collector
  -> report_builder and FinancialConfidenceExtractor
  -> validation and artifact envelope
  -> research_schema.json
```

The post-processor runs after the Agent run, not inside AgentLoop.

Why the MVP does not mutate AgentLoop:

* Schema generation is a product projection, not reasoning-loop behavior.
* Trace completeness and schema rules will continue to evolve.
* A post-processor is easier to test from fixtures, retry, version, disable,
  and roll back.
* A schema failure must never change tool execution or final-answer delivery.

## 3. Storage Layout

Production location:

```text
agent/runs/<run_id>/
  trace.jsonl
  request.json
  artifacts/
    research_schema.json
    research_schema.meta.json
```

Policy:

* One canonical artifact per run per active schema version.
* The MVP filename is research_schema.json for the active version.
* The meta sidecar is optional in the first implementation, but recommended
  for generator provenance, validation status, and error summaries.
* Development observations belong only under ignored local_reports/ and must
  never be presented as production artifacts.
* Existing runs without an artifact remain valid historical runs.

## 4. Artifact Envelope and Versioning

The artifact adds an envelope around the established Research Report Schema:

```json
{
  "schema_version": "1.0",
  "artifact_type": "research_schema",
  "generated_at": "2026-07-13T00:00:00Z",
  "generator": {
    "name": "research_schema_post_processor",
    "version": "1.0"
  },
  "run_id": "<run_id>",
  "generation_status": "complete",
  "source_trace": {
    "path": "trace.jsonl",
    "event_count": 0,
    "tool_result_count": 0
  },
  "report": { }
}
```

Version rules:

* schema_version is semantic: major for breaking field meaning/removal, minor
  for backward-compatible additions.
* Consumers must ignore unknown additive fields.
* A future migration reads an old artifact and writes a new version without
  overwriting the original until validation succeeds.
* The run_id is immutable; generated_at records artifact creation time, not
  market-data time.
* report remains the existing UI-independent Research Report Schema.

## 5. Generation Rules

| Run outcome | Generate artifact? | generation_status | Rule |
| --- | --- | --- |
| Successful run with usable trace | Yes | complete or partial | Generate after validation; schema completeness decides complete/partial. |
| Successful run with incomplete trace/tool data | Yes | partial | Preserve limitations and collector warnings. |
| Run ends failed but trace has useful verified results | Optional, controlled MVP policy | partial | Only write if report can identify its incomplete/failure context without invented fields. |
| Failed run with no usable trace | No report artifact | failed metadata only | Do not create an empty report that looks valid. |
| Schema post-processor failure | No replacement artifact | failed metadata/log | Keep trace and any prior validated artifact intact. |

Initial MVP recommendation: generate artifacts only for completed runs, and
allow complete or partial status. Failed-run artifacts should wait for a later
explicit product decision.

## 6. Schema Completeness Rules

Artifact generation status is program-calculated, never LLM-generated.

| Status | Minimum condition |
| --- | --- |
| complete | Confirmed symbol, market result where requested, income/balance/cashflow confidence present, data confidence present, and no fatal collector error. |
| partial | Schema generated but a requested capability, core statement, source field, reporting period, or trace field is missing/failed/blocked. |
| failed | Post-processor cannot safely identify the symbol, read the trace, or build a schema. No report artifact is written. |

Warnings and missing capabilities must be retained in the artifact. A partial
artifact is useful only when its limitations are displayed prominently.

## 7. Failure Handling and Observability

| Failure | Behavior | Recorded evidence |
| --- | --- | --- |
| Trace missing/unreadable | Do not write report artifact. | meta status failed, safe error code, run_id. |
| Tool result offload unavailable | Build only if required tool result can be resolved; otherwise partial or failed per capability. | collector warning and missing capability. |
| Tool result missing | Generate partial only if symbol and remaining data are safe. | statement/tool warning. |
| Financial confidence missing | Generate partial only; do not synthesize provider or period. | financial confidence warning. |
| Report builder exception | Do not overwrite a prior valid artifact. | meta status failed and safe exception category. |
| Existing artifact present | Write atomically to temp then replace only after validation. | previous artifact preserved on failure. |

The post-processor should write compact machine-readable error codes, not raw
provider payloads, credentials, or full stack traces into the artifact.

## 8. Security and Data Boundary

The artifact may contain only research report facts, report metadata, source
attribution, data-quality status, warnings, and bounded AI interpretation.

It must not contain:

* API keys, tokens, OAuth material, environment-variable values, or local
  absolute configuration paths.
* Raw trace prompts/results beyond fields explicitly selected for the report.
* Shell command content, file-system listings, or tool-output sidecars.
* Private documents or unredacted web content unless a later, explicit data
  policy permits them.
* Hidden chain-of-thought or internal reasoning events.

Artifact writing uses the existing ignored agent/runs directory. The artifact
must never be Git-tracked by default.

## 9. Web UI Consumption Contract

The future Web UI reads the artifact by run_id:

```text
Web UI
  -> run/attempt reference
  -> research_schema.json
  -> render report sections and data-confidence disclosures
```

The Web UI must not parse trace.jsonl. Trace remains a debugging/audit view for
authorized users and is intentionally more verbose, unstable, and sensitive.

UI behavior:

* Render Research Workspace sections from report fields.
* Show generation_status and data-confidence warnings before narrative.
* Show partial/missing sections explicitly rather than blank cards.
* Link to trace/audit details only through a controlled future endpoint.
* Treat an absent artifact as 'not generated', not as a zero-data report.

## 10. Testing Strategy

Implementation begins fixture-first:

1. Complete trace fixture -> artifact envelope -> schema version, run_id,
   report sections, and complete status.
2. Partial financial fixture -> partial artifact with statement warnings.
3. Fallback fixture -> provider/source/fallback fields preserved.
4. Missing final answer -> artifact remains structured with memo placeholder.
5. Missing trace -> no artifact write and safe failure metadata.
6. Existing artifact plus generation failure -> original artifact unchanged.
7. JSON serialization and schema-version validation.

Controlled historical and real-trace observation comes only after fixtures pass.
The first real test writes to ignored local_reports, not to an agent/runs
artifact directory.

## 11. Rollback

Artifact generation is a post-run optional step. Rollback means disabling or
removing the post-processor invocation and leaving AgentLoop, trace files,
tool execution, and existing report builder behavior unchanged. Existing valid
artifacts remain readable by their schema version.

## 12. Implementation Gate

Before code is approved, decide:

1. The exact completed-run trigger location outside AgentLoop.
2. Whether the first production writer creates the optional meta sidecar.
3. The atomic-write and validation helper contract.
4. The API/read endpoint ownership after artifact format stabilizes.

Recommended next task: design a fixture-only artifact generator interface and
acceptance tests. Do not write an artifact from a real run until that proof is
complete.

## 13. Fixture-only Generator Proof Status (2026-07-13)

Implemented:

* Added a pure in-memory artifact envelope generator.
* It delegates trace fixture conversion to the existing trace collector and
  report builder pipeline.
* It creates complete, partial, or failed envelope states without reading a
  trace from disk or writing a production artifact.
* Tests serialize only to a TemporaryDirectory research_schema.json file.

Boundary:

* No AgentLoop, live data, Web UI, agent/runs artifact, provider-chain, loader,
  or credential interaction occurred.
