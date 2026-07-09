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

### 1. Data Freshness & Anti-Hallucination Guardrails

* Type: improvement / safety guardrail.
* Impact area: all market-data-backed research reports.
* Priority: highest.
* Suggested phase: Phase 1 before `a-stock-data` production integration.
* Requires business code change: yes.
* Current status: `get_market_data` freshness metadata MVP implemented; Source Summary In Reports MVP implemented; Time-sensitive Report Gate MVP implemented; extended data-quality contract for `get_fund_flow`, `get_stock_news`, and `get_research_reports` implemented; No Estimate Guard MVP implemented.
* Design document: `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
* ADR: `ADR-008: LLM Must Not Invent Market Data`.
* Implementation files: `agent/src/data_quality/freshness.py`, `agent/src/data_quality/report_summary.py`, `agent/src/data_quality/report_gate.py`, `agent/src/data_quality/no_estimate.py`, `agent/src/market_data.py`, `agent/src/tools/fund_flow_tool.py`, `agent/src/tools/stock_news_tool.py`, `agent/src/tools/research_reports_tool.py`, `agent/src/agent/context.py`, `agent/src/agent/loop.py`, `agent/tests/test_data_freshness.py`, `agent/tests/test_report_data_source_summary.py`, `agent/tests/test_report_gate.py`, `agent/tests/test_extended_data_quality.py`, `agent/tests/test_no_estimate_guard.py`.
* Core principle: LLM must not invent market data.
* Acceptance focus: if today's data is missing, stale, failed, delayed, or timestamp-unknown, the report must disclose that instead of inventing price, volume, turnover, fund-flow, news, or financial facts.
* Recommended next step: retest the Web UI red-light prompt and then extend metadata to remaining tools if gaps persist.
* Main remaining risk: the hard gate only covers `get_market_data`; No Estimate Guard warns but does not rewrite unsafe estimated sentences.
* 2026-07-07 Web UI retest: passed for Source Summary, multi-tool metadata display, stale-news disclosure, and No Estimate Warning. Main body still contained estimated market-fact phrasing, confirming warning-only behavior.

### 1a. Stricter No Estimate Guard

* Type: improvement / safety guardrail.
* Impact area: explicit no-estimate prompts in final reports.
* Priority: medium-high if warning-only behavior is not acceptable.
* Suggested phase: after Symbol Normalizer decision, or before it if the product requirement becomes strict body-level prevention.
* Requires business code change: yes.
* Current behavior: appends `No Estimate Warning` but does not rewrite the report body.
* Candidate next behavior: move estimated market-fact sentences into an `Invalid Estimated Claims` section, or block with a Data Insufficient-style report when explicit no-estimate prompts produce estimated market numbers.
* Main risk: overly aggressive rewrite may remove valid tool-returned facts that merely contain approximate wording.

### 2. Symbol Normalization

* Type: improvement.
* Impact area: data source routing, Agent tool calling, report consistency.
* Priority: high.
* Suggested phase: Phase 1 foundation task.
* Requires business code change: yes for tool integration; design/helper already complete.
* Current status: pure helper, acceptance-style tests, integration plan, and feature-flagged `get_market_data` integration implemented.
* Acceptance focus: natural inputs such as `QQQ`, `600519`, `00700`, `贵州茅台`, and ambiguous multi-listing names.
* Implementation files: `agent/src/symbols/normalizer.py`, `agent/src/symbols/config.py`, `agent/src/market_data.py`, `agent/tests/test_symbol_normalizer.py`, `agent/tests/test_market_data_symbol_normalization.py`.
* Integration plan: `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
* Recommended next step: Web UI bare-symbol retest with `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1` set only for the local test run.
* Main risk: ambiguous inputs such as `000001` and accidental changes to currently working explicit symbols.
* Current mitigation: feature flag defaults off; bare `000001` and Chinese names require confirmation and do not force provider calls.

### 2a. Pre-Tool Symbol Intent Guard

* Type: bug / safety improvement.
* Impact area: Web UI Agent tool calling, ambiguous symbols, Chinese-name inputs.
* Priority: high.
* Suggested phase: before default-enabling Symbol Normalizer.
* Requires business code change: yes.
* Observed in Web UI retest: the Agent converted `000001` into `000001.SZ` and `贵州茅台` into `600519.SH` before `get_market_data` saw the original user text.
* Why it matters: a tool-entry normalizer cannot require confirmation if the raw ambiguous input has already been rewritten into an explicit symbol.
* Candidate solution: capture raw symbol intent from the user prompt, pass `raw_input` or `original_query` into tools, or add a pre-tool guard that blocks ambiguous/name-based conversions until confirmed.
* Current mitigation: keep `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0` by default and prefer explicit symbols for production-like tests.
* Design document: `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`.
* Recommended next step: implement pure `evaluate_symbol_intent_guard(...)` plus tests before any AgentLoop integration.
* Current implementation status: pure function and tests are complete; AgentLoop integration is not started.
* Implementation files: `agent/src/symbols/intent_guard.py`, `agent/tests/test_symbol_intent_guard.py`.
* AgentLoop integration status: feature-flagged integration complete for `get_market_data`; Web UI retest completed on 2026-07-08.
* Web UI retest result: partial pass.
* Passed in Web UI:
  * `600519`, `QQQ`, `00700`, and explicit `600519.SH` were not incorrectly blocked.
  * `get_market_data` was blocked for ambiguous `000001` and Chinese-name `贵州茅台`.
  * Final answers asked for clarification instead of giving a normal market report for `000001` and `贵州茅台`.
* Remaining defect:
  * `000001` still triggered other stock-specific tools with `000001.SZ`, including `get_fund_flow`, `get_stock_news`, and `get_sector_info`.
  * `贵州茅台` still triggered other stock-specific tools with `600519.SH`, including `get_stock_news` and `get_sector_info`.
* Why it matters: the current guard prevents the primary market-data provider call, but it does not yet prevent all provider calls based on an unconfirmed symbol intent.
* Recommended next step: extend the feature-flagged guard to all stock-specific provider tools or add a per-run symbol-intent confirmation gate before any stock-specific provider tool executes.
* Current implementation update: first-batch stock-specific tool coverage is implemented for `get_market_data`, `get_fund_flow`, `get_stock_news`, `get_research_reports`, and `get_sector_info`.
* Still not covered: `web_search`, `read_url`, `search_symbol`, and `read_document`.
* Current validation status: unittest, lightweight mock validation, and Web UI stock-specific guard retest passed.
* Web UI pass details: `000001` and `贵州茅台` no longer reached first-batch stock-specific providers before clarification; `600519` and `600519.SH` remained allowed.
* Remaining validation before default-enable: boundary retest for `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.
* Default-enable recommendation: not yet.

### 3. A-Share Data Source Enhancement

* Type: improvement / research.
* Impact area: A-share market data, fund flow, announcements, news, research reports.
* Priority: high.
* Suggested phase: after proving gaps with real trading-day records and after freshness guardrails are planned.
* Requires business code change: yes if adapter is implemented.
* Important dependency: any `a-stock-data` adapter should follow the freshness metadata and source-failure contract before production research use.

### 4. Custom Provider Plugin Framework

* Type: improvement.
* Impact area: maintainability, upstream compatibility, safer local extensions.
* Priority: medium.
* Suggested phase: Phase 1 design.
* Requires business code change: design first; implementation later.
* Dependency: provider framework should inherit the freshness contract.

### 5. LLM Router

* Type: improvement.
* Impact area: model cost, quality, task specialization.
* Priority: medium.
* Suggested phase: after data-source and symbol basics are clearer.
* Requires business code change: yes if implemented.

### 6. Data Source Call Visualization

* Type: improvement.
* Impact area: user trust, auditability, debugging.
* Priority: medium.
* Suggested phase: product stabilization.
* Requires business code change: likely yes.
* Dependency: should display freshness status and source failures when available.

### 7. Research Report Export Experience

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
## Added 2026-07-08: Asset-type-aware Tool Routing

Type: improvement

Impact range:

Index prompts such as `000001.SH` may call stock-specific tools or market-wide tools without enough asset-type context. In the boundary retest, `get_market_data` handled `000001.SH`, but `get_sector_info` was blocked because the tool call did not include an auditable symbol.

Priority:

Medium-high before default-enabling symbol guard / normalizer.

Suggested phase:

Phase 1 hardening, after the stock-specific symbol guard boundary retest.

Needs business code change:

Yes. Likely requires tool routing or tool metadata changes so the Agent can distinguish stock, ETF, index, sector, and market-wide tasks.

Current handling:

Record only. Do not fix in this retest round.

Design status:

Initial design added in `docs_local/ASSET_TYPE_AWARE_TOOL_ROUTING_DESIGN.md`.

Proposed MVP tools:

* `get_sector_info`
* `get_financial_statements`
* `get_shareholder_count`
* `get_margin_trading`
* `get_block_trades`

Decision:

This should be handled before default-enabling Symbol Normalizer or Pre-tool Symbol Guard.

Implementation status:

Pure function and unit tests are complete. Runtime integration is not yet done.

Next engineering item:

Feature-flagged AgentLoop integration with structured routing metadata and no provider call on `block` / `ask_for_confirmation`.

Current engineering status:

Feature-flagged AgentLoop integration is complete. Web UI retest is still pending.

Parallel execution fix status:

The first Web UI retest found that parallel readonly tool batches skipped Asset-type Routing Guard. This has been fixed in `AgentLoop._execute_parallel` with tests. Web UI retest is still required before default-enable decisions.

Market-wide news guard status:

The same Web UI retest found that `get_stock_news(scope=global)` was blocked by Symbol Intent Guard. This has been fixed for market-wide news calls. Symbol-specific news calls remain guarded.

Next validation item:

Run local Web UI retest with:

* `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1`
* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`
* Optional controlled `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`

Specific retest cases:

* `510300.SH` + financial statements should be blocked before provider execution.
* `QQQ.US` + stock news should warn and include `_tool_routing_guard`.
* `get_stock_news(scope=global)` should not be blocked by Symbol Intent Guard.

## Added 2026-07-08: Market-wide Benchmark Routing Policy

Type:

Improvement / research.

Impact range:

Market-wide prompts such as "analyze broad market news" may reasonably require benchmark indices or market aggregates. After safety guards are default-on, invented or untraceable symbols are blocked by design. A separate policy is needed to define which benchmark symbols can be used for broad market requests and how to disclose them.

Priority:

Medium-high before broad market research workflows are productized.

Suggested phase:

Phase 1 hardening, before `a-stock-data` adapter work.

Needs business code change:

Likely yes, but start with a design document.

Current handling:

Record only. Do not loosen Symbol Intent Guard ad hoc.

Acceptance direction:

* Define approved benchmark sets for A-share, US, HK, ETF, and global-market prompts.
* Require trace disclosure when the system selects a benchmark not typed by the user.
* Keep single-stock prompts under strict symbol-intent rules.
* Preserve `get_stock_news(scope=global)` market-wide exemption.

Design status:

Design document added: `docs_local/MARKET_WIDE_BENCHMARK_ROUTING_POLICY.md`.

Next engineering step:

Implement a pure benchmark policy helper and tests only after user approval.

Implementation status:

Pure helper and tests are complete:

* `agent/src/symbols/benchmark_policy.py`
* `agent/tests/test_benchmark_policy.py`

Remaining work:

* Feature-flagged integration into Symbol Intent Guard.
* Trace/report metadata for `system_selected_benchmark`.
* Web UI retest after integration.

Current status:

Feature-flagged AgentLoop integration is complete. `_benchmark_policy` metadata is attached to allowed benchmark tool results. The next backlog item is Web UI retest; final report `Benchmark Selection Summary` is still future work.

Batch fix status:

* Web UI/API same-origin retest found an A-share batch issue: `000688.SH` appeared in a batch with valid benchmarks.
* The fix now blocks mixed batches as a whole and discloses:
  * `requested_symbols`
  * `allowed_symbols`
  * `rejected_symbols`
  * `benchmark_universe`
* `000688.SH` is correctly reported as rejected; valid benchmarks such as `000001.SH` are no longer implied as the rejection cause.

Remaining work:

* Re-run targeted Web UI/API same-origin retest after this fix.
* Keep benchmark policy default off until the retest passes.
* Add final report `Benchmark Selection Summary` only after runtime behavior is stable.

## Added 2026-07-09: a-stock-data Adapter Planning

Type:

Research / improvement.

Impact range:

A-share data-source enhancement. This affects financial statements, fund flow, research reports, news, sector information, and possibly market data later.

Priority:

High after Phase 1 guardrails; still design-first before code integration.

Current status:

Design document added: `docs_local/A_STOCK_DATA_ADAPTER_DESIGN.md`.

Recommended MVP:

Tool-level A-share financial statements fallback, behind `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0` by default.

Why this first:

* It is useful for investment research.
* It is company-specific, so Asset-type Routing Guard can clearly block indexes and ETFs before adapter execution.
* It is less time-sensitive than intraday fund flow.
* It does not disturb the existing market-data fallback chain.

Explicit non-goals:

* Do not replace the current A-share market-data fallback chain.
* Do not vendor-copy the upstream Skill into this repository.
* Do not bypass Symbol Guard, Asset-type Routing Guard, Freshness Guard, Source Summary, or Report Gate.
* Do not use iwencai key-gated semantic search in the MVP.

Next engineering step:

Pure adapter normalization helpers and tests only; no live provider calls.
