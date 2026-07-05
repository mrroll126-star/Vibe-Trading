# Product Backlog

Status: open backlog for local investment research productization.

This backlog records observed defects, product gaps, and future improvement candidates. Items here are not approved for implementation unless the user explicitly confirms a task.

## Bug / Defect

### 1. Reports Page Stays On Loading

* Type: bug
* Observed: 2026-07-05 Web UI smoke test.
* Symptom: opening `/reports` in the frontend showed `Loading...` and did not render a usable report list during the quick check.
* Reproduction:
  1. Start backend on `127.0.0.1:8899`.
  2. Start frontend on `127.0.0.1:5899`.
  3. Open `http://127.0.0.1:5899/reports`.
* Impact: report discovery/export workflow is unclear from Web UI. Agent session pages still show generated reports, so research task execution is not blocked.
* Priority: medium.
* Suggested phase: Phase 1 product stabilization, after trading-day testing.
* Blocks 2026-07-06 A-share test: no.
* Requires business code change: likely yes, frontend/API investigation.

### 2. `/runs` List Shows A-Share Run As `unknown`

* Type: bug
* Observed: 2026-07-05 Web UI A-share task.
* Symptom: `/runs` list showed `20260705_164700_99_303723` as `unknown`, while `/runs/20260705_164700_99_303723`, Web session messages, and session trace showed success.
* Reproduction:
  1. Run a Web UI Agent task for `600519.SH`.
  2. Compare `/runs` list with `/runs/<run_id>` detail and local session trace.
* Impact: history/status overview can mislead users even when the actual task completed.
* Priority: medium-high.
* Suggested phase: Phase 1 product stabilization if it affects daily workflow.
* Blocks 2026-07-06 A-share test: no, if detailed endpoint/trace are checked.
* Requires business code change: likely yes, run-list status mapping or state persistence.

### 3. yfinance TLS / Yahoo Profile Connection Reset

* Type: bug / environment compatibility.
* Observed: repeated across preflight, US smoke test, SPY/600519/300750 research tasks.
* Symptom: yfinance and Yahoo profile-style calls can fail with curl/OpenSSL TLS errors or connection reset.
* Impact: yfinance-backed US/HK/profile flows are unreliable in this local environment.
* Priority: medium.
* Current handling strategy: record only; do not fix yet.
* Suggested phase: after trading-day validation and symbol normalization.
* Blocks 2026-07-06 A-share test: no.
* Requires business code change: unknown; may be environment/dependency fix.

### 4. Some A-Share Secondary Providers Fail Or Are Missing Dependencies

* Type: bug / environment gap.
* Observed: 2026-07-05 A-share preflight.
* Symptom: `mootdx` and `baostock` dependencies are missing, Tushare token is not configured, Eastmoney and some AkShare requests returned no rows or connection interruptions.
* Impact: Tencent currently carries the basic A-share OHLCV path; fallback breadth is weaker than the provider list suggests.
* Priority: medium.
* Suggested phase: Phase 1 data-source stabilization.
* Blocks 2026-07-06 A-share test: no, because Tencent worked for all six preflight symbols.
* Requires business code change: not necessarily; may be dependency/config/data-source planning.

## Improvement

### 1. Symbol Normalization

* Type: improvement.
* Impact area: data source routing, Agent tool calling, report consistency.
* Priority: high.
* Suggested phase: Phase 1 foundation task.
* Requires business code change: design first; implementation later.
* Current status: design and acceptance plan created in `SYMBOL_NORMALIZATION_DESIGN.md` and `SYMBOL_NORMALIZATION_ACCEPTANCE_TESTS.md`.
* Acceptance focus: natural inputs such as `QQQ`, `600519`, `00700`, `贵州茅台`, and ambiguous multi-listing names.

### 2. A-Share Data Source Enhancement

* Type: improvement / research.
* Impact area: A-share market data, fund flow, announcements, news, research reports.
* Priority: high.
* Suggested phase: after proving gaps with real trading-day records.
* Requires business code change: yes if adapter is implemented.

### 3. Custom Provider Plugin Framework

* Type: improvement.
* Impact area: maintainability, upstream compatibility, safer local extensions.
* Priority: medium.
* Suggested phase: Phase 1 design.
* Requires business code change: design first; implementation later.

### 4. LLM Router

* Type: improvement.
* Impact area: model cost, quality, task specialization.
* Priority: medium.
* Suggested phase: after data-source and symbol basics are clearer.
* Requires business code change: yes if implemented.

### 5. Data Source Call Visualization

* Type: improvement.
* Impact area: user trust, auditability, debugging.
* Priority: medium.
* Suggested phase: product stabilization.
* Requires business code change: likely yes.

### 6. Research Report Export Experience

* Type: improvement.
* Impact area: daily workflow, archiving, sharing with the user's own notes.
* Priority: medium.
* Suggested phase: after Reports page loading issue is understood.
* Requires business code change: likely yes.

## Not Approved

The following are not approved yet:

* Replacing provider chains.
* Integrating `a-stock-data`.
* Fixing yfinance through dependency or code changes.
* Enabling shell tools.
* Adding trading execution.
* Exposing Web UI remotely.
