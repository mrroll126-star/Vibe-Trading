# Local Roadmap

This file tracks the local long-term plan for maintaining a private research version of Vibe-Trading.

## Phase 0: Bootstrap Local Setup

Status: completed on 2026-07-05.

Goal: create a clean, auditable local base without changing upstream business logic.

Planned steps:

1. Clone the original upstream project from `HKUDS/Vibe-Trading`.
2. Create local branches:
   - `main`: keep aligned with upstream.
   - `dev`: long-term local integration branch.
   - `feature/bootstrap-local-setup`: today's initialization branch.
3. Create the `docs_local/` project management folder.
4. Read the project structure.
5. Attempt basic local deployment in a later step.
6. Produce a Tailscale access plan in a later step.
7. If there is enough time and usage budget later, add a US data source smoke test.

## Git Remote Strategy

Current state:

- `origin` points to `https://github.com/HKUDS/Vibe-Trading`.
- No personal GitHub fork has been configured yet.
- No push should be performed until the user creates a fork and confirms the target.

Recommended future state:

- `origin`: the user's personal fork.
- `upstream`: `https://github.com/HKUDS/Vibe-Trading`.

Suggested future commands after the fork exists:

```bash
git remote rename origin upstream
git remote add origin https://github.com/<your-github-user>/Vibe-Trading.git
git fetch --all
```

## Branch Model

- `main`: only sync from upstream.
- `dev`: long-term local integration.
- `feature/*`: one feature or setup task per branch.
- Backup tags: create a local tag before syncing upstream into local work.

## Phase 0 Result

Completed:

1. Environment setup and dependency installation.
2. Local backend/frontend run verification.
3. Architecture discovery and documentation.
4. API auth local setup.
5. Tailscale remote-access design, later deferred by user decision.
6. US data-source smoke test script.
7. DeepSeek provider verification.
8. Minimal native Agent research task.
9. Web UI product smoke test with `SPY.US` and `600519.SH`.

See:

* `docs_local/PHASE_0_BOOTSTRAP_SUMMARY.md`
* `docs_local/TEST_REPORT.md`
* `docs_local/MINIMAL_RESEARCH_TASK.md`
* `docs_local/WEB_UI_SMOKE_TEST_REPORT.md`

## Phase 1 Plan

Status: proposed.

Recommended order:

1. A-share trading-day validation using existing providers.
2. Data Freshness & Anti-Hallucination Guardrails implementation planning.
3. `get_market_data` freshness wrapper.
4. Data Source Summary / Missing Data / Source Failures in reports.
5. Symbol normalizer integration for `get_market_data`.
6. `a-stock-data` adapter planning.
7. Custom provider plugin framework design.
8. LLM router design.

Phase 1 foundation update:

* Data Freshness & Anti-Hallucination Guardrails are now the highest-priority Phase 1 safety foundation.
* Data freshness and anti-hallucination work must happen before `a-stock-data` is integrated into production research workflows.
* The core principle is: LLM must not invent market data.
* Design document:
  * `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`
* Symbol normalization design is now a high-priority foundation task because it directly affects natural user inputs, tool routing, data-source selection, and future A-share adapter safety.
* The pure symbol normalizer helper and unittest coverage are implemented.
* First tool integration is now implemented only for `get_market_data`, behind disabled-by-default `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`.
* Broad integration is still not approved. `get_stock_news`, `get_fund_flow`, and `get_research_reports` are not connected to the normalizer yet.
* Web UI bare-symbol retest has been completed with the flag enabled only for the test run.
* Result: `get_market_data` compatibility passed and `_data_quality` remained intact, but the Agent can pre-normalize ambiguous or named inputs before the tool-entry normalizer sees the raw input.
* The next recommended design task is a pre-tool symbol intent guard before any default-enable decision.
* Design documents:
  * `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`
  * `docs_local/SYMBOL_NORMALIZATION_ACCEPTANCE_TESTS.md`
  * `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`
  * `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`

Pre-tool Symbol Intent Guard update:

* Design is complete.
* Pure guard function with tests is complete.
* AgentLoop integration is feature-flagged.
* First-batch stock-specific tool coverage is implemented:
  * `get_market_data`
  * `get_fund_flow`
  * `get_stock_news`
  * `get_research_reports`
  * `get_sector_info`
* Feature flag: `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`.
* Current default: on after Web UI retests and default policy review.
* Web UI retest after the expanded guard passed for `000001`, `贵州茅台`, `600519`, and `600519.SH`.
* Default-enable review: completed; guard is now default-on.
* `a-stock-data` remains deferred until symbol identity and data quality are auditable.

Current implementation files:

* `agent/src/symbols/intent_guard.py`
* `agent/tests/test_symbol_intent_guard.py`
* `agent/tests/test_symbol_intent_guard_integration.py`

See:

* `docs_local/PHASE_1_PLAN.md`
* `docs_local/NEXT_TASKS.md`
* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`
## 2026-07-08 Boundary Retest Milestone

Completed:

* Web UI boundary retest with `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`.
* Web UI boundary retest with `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`.
* Verified safe bare US ticker: `QQQ -> QQQ.US`.
* Verified safe bare HK code: `00700 -> 00700.HK`.
* Verified explicit A-share stock: `000001.SZ`.
* Verified explicit A-share index market-data path: `000001.SH`.

New Phase 1 hardening item:

* Asset-type-aware tool routing for stock / ETF / index / sector / market-wide prompts.

Default-enable decision:

* Pre-tool Symbol Guard: now default-on after user approval and retests.
* Symbol Normalizer: keep feature-flagged for now.

## 2026-07-08 Asset-type-aware Routing Design

Completed:

* Read-only tool compatibility investigation.
* Added `docs_local/ASSET_TYPE_AWARE_TOOL_ROUTING_DESIGN.md`.
* Defined MVP asset types: stock, index, ETF, fund, unknown.
* Drafted compatibility matrix for market data, stock-specific, disclosure, flow, and web tools.
* Defined proposed future pure function `evaluate_tool_asset_compatibility`.

Phase 1 priority update:

* Asset-type-aware routing should come before default-enabling Symbol Normalizer / Pre-tool Symbol Guard.
* `a-stock-data` remains downstream.

## 2026-07-08 Pure Asset-type Guard Implementation

Completed:

* Added pure guard module `agent/src/tools/routing_guard.py`.
* Added unit tests `agent/tests/test_tool_routing_guard.py`.
* Confirmed no AgentLoop integration and no runtime behavior change.
* Confirmed no provider-chain, loader, or Web UI changes.

Next:

* Feature-flagged AgentLoop integration.
* Web UI retest for stock / ETF / index routing.
* Default-enable decision for Symbol Guard / Symbol Normalizer after retest.

## 2026-07-08 Feature-flagged Asset Routing Integration

Completed:

* Added `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD`.
* Integrated asset-type routing guard into AgentLoop after symbol intent guard.
* Preserved zero behavior change when flag is off.
* Added integration tests for allow / warn / block / ask / non-covered tools / ordering.

Next:

* Web UI retest asset-type routing.
* Decide whether Pre-tool Symbol Guard can become default-on.
* Keep Symbol Normalizer and `a-stock-data` deferred until retests pass.

## 2026-07-08 Parallel Asset Routing Fix

Completed:

* Fixed Asset-type Routing Guard for parallel readonly tool execution.
* Unified single and parallel pre-tool guard order.
* Preserved Symbol Intent Guard priority.
* Allowed market-wide `get_sector_info(mode=ranking|list|overview)` without a single symbol.
* Added parallel-path tests for block / warn / flag off / non-covered tools.

Next:

* Repeat Web UI asset-type routing retest.
* Decide default policy only after Web UI retest passes.
* Keep `a-stock-data` deferred.

## 2026-07-08 Market-wide Stock News Guard Fix

Completed:

* Allowed market-wide `get_stock_news` calls through Symbol Intent Guard.
* Preserved guard behavior for symbol-specific `get_stock_news`.
* Added pure and AgentLoop integration tests.
* Confirmed `get_sector_info(mode=ranking)` remains allowed.

Next:

* Run directional Web UI retest for asset routing and market-wide news.
* Decide safety guard default policy only after retest passes.
* Keep `a-stock-data` deferred.

## 2026-07-08 Safety Guard Default Policy

Completed:

* Pre-tool Symbol Intent Guard is now default-on.
* Asset-type Routing Guard is now default-on.
* Symbol Normalizer remains default-off.
* All three feature flags remain available for local override.

Why:

The two default-on features are safety guards. They prevent unsafe execution:

* ambiguous or untraceable symbols reaching stock-specific tools;
* unsuitable tool / asset-type combinations reaching providers.

Symbol Normalizer is different because it automatically rewrites user input, so it remains opt-in.

Next roadmap item:

Design Market-wide Benchmark Routing Policy before adding new providers such as `a-stock-data`.

## 2026-07-08 Market-wide Benchmark Routing Policy Design

Completed:

* Added `docs_local/MARKET_WIDE_BENCHMARK_ROUTING_POLICY.md`.
* Defined user-specified target intent, market-wide intent, and ambiguous intent.
* Proposed MVP benchmark universe for A-share, US, and HK market-wide prompts.
* Defined reporting requirement: Benchmark Selection Summary.
* Confirmed this is a narrow exception, not a Symbol Guard bypass.

Next roadmap item:

Implement pure benchmark policy helper and tests after user approval.

Still deferred:

* `a-stock-data` adapter.
* Provider-chain changes.
* Web UI changes.

## 2026-07-08 Pure Market-wide Benchmark Policy

Completed:

* Added pure helper `evaluate_market_wide_benchmark_intent(...)`.
* Added MVP benchmark universe constants for A-share, US, and Hong Kong markets.
* Added unit tests covering market-wide, ambiguous, single-target, company-specific tool, and benchmark-universe boundaries.
* Confirmed symbol/routing/anti-hallucination regressions still pass.

Not changed:

* AgentLoop.
* Symbol Intent Guard runtime behavior.
* Asset-type Routing Guard runtime behavior.
* Feature flag defaults.
* Provider chain / loaders / Web UI.

Next roadmap item:

Feature-flagged integration into Symbol Intent Guard, only after user approval.

## 2026-07-08 Feature-flagged Benchmark Policy Integration

Completed:

* Added `VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY`.
* Integrated benchmark policy into AgentLoop pre-tool guard path.
* Preserved default-off behavior.
* Added structured block / confirmation results.
* Added `_benchmark_policy` metadata to allowed benchmark tool results.
* Added integration tests.

Not changed:

* Provider chains.
* Loaders.
* Web UI.
* `a-stock-data`.

Next roadmap item:

Targeted Web UI retest with the benchmark policy flag enabled.

## 2026-07-08 Benchmark Batch Handling Fix

Completed:

* Fixed benchmark policy batch validation.
* Added clear disclosure of `requested_symbols`, `allowed_symbols`, `rejected_symbols`, and `benchmark_universe`.
* Preserved conservative behavior: if any requested symbol is outside the approved universe, the whole batch is blocked.
* Added tests for A-share, US, HK, mixed batches, comma-separated strings, and flag-off behavior.

Still default off:

* `VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY`

Next roadmap item:

Run targeted Web UI/API same-origin retest for A-share benchmark batches before considering any broader rollout.

## 2026-07-09 a-stock-data Adapter Design

Completed:

* Confirmed the Phase 1 guardrail baseline is strong enough to start A-share data-source enhancement planning.
* Read current Vibe-Trading A-share data-source and tool structure.
* Read `a-stock-data` README / SKILL / LICENSE / changelog from a readonly vendor clone outside the project repository.
* Added `docs_local/A_STOCK_DATA_ADAPTER_DESIGN.md`.
* Recommended a tool-level MVP instead of replacing the market-data provider chain.

Status update:

* Benchmark Policy MVP passed the batch-fix API/Web UI same-origin retest.
* Benchmark Policy remains default off because it is product behavior, not only a safety brake.
* `a-stock-data` remains design-only; no integration code has been written.

Recommended next roadmap item:

Build pure adapter normalization helpers and tests for the recommended MVP, without provider calls or tool integration.

## 2026-07-09 a-stock-data Financial Normalizer Phase B

Completed:

* Added a pure `a-stock-data` financial normalizer helper.
* Added tests for normal rows, Chinese date fields, empty/error payloads, malformed input, rows without dates, warnings, nested rows, and Source Summary contract keys.
* Confirmed existing anti-hallucination, symbol guard, routing guard, and benchmark policy regression tests still pass.

Not changed:

* Provider chains.
* Loader registry.
* `get_financial_statements` runtime behavior.
* Web UI.
* Dependency set.
* Runtime services.

Next roadmap item:

Design feature-flagged `get_financial_statements` integration before any live `a-stock-data` calls.

## 2026-07-09 GitHub Remote Backup Strategy

Completed:

* Confirmed current `origin` still points to HKUDS/Vibe-Trading.
* Confirmed current branch has no tracking branch and local Phase 1 commits are not pushed.
* Confirmed ignored sensitive/runtime paths remain untracked.
* Added `docs_local/GITHUB_REMOTE_STRATEGY.md`.

Recommended next roadmap item:

User creates a GitHub fork, then local remotes are changed to:

```text
origin   = user fork
upstream = HKUDS/Vibe-Trading
```

Then push only `feature/bootstrap-local-setup` to the user's fork after explicit user confirmation.

## 2026-07-09 GitHub Remote Backup Completed

Completed:

* Created the user's fork under `mrroll126-star/Vibe-Trading`.
* Reconfigured remotes:
  * `origin` points to the user's fork through a project-specific SSH alias.
  * `upstream` points to `HKUDS/Vibe-Trading`.
* Pushed `feature/bootstrap-local-setup` to the user's fork.
* Confirmed the remote branch points to `01bbc89`.
* Confirmed sensitive/runtime paths remain ignored and untracked.

Next roadmap item:

Continue with `get_financial_statements` feature-flagged fallback integration design.

## 2026-07-09 a-stock-data Financial Statements Phase C Design

Completed:

* Added `docs_local/A_STOCK_DATA_FINANCIALS_INTEGRATION_PLAN.md`.
* Confirmed current `get_financial_statements` source routing:
  * A-share: Eastmoney.
  * Hong Kong: Eastmoney HK F10.
  * US: SEC EDGAR.
* Defined a conservative fallback-only design for confirmed A-share stocks.
* Kept the default flag off:
  * `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0`
* Required `_data_quality` and Source Summary compatibility.

Not changed:

* No business code.
* No provider chain.
* No loader registry.
* No Web UI.
* No live public endpoint call.
* No `a-stock-data` runtime integration.

Next roadmap item:

If approved, implement the feature-flagged `get_financial_statements` fallback with mock tests first.

## 2026-07-09 a-stock-data Financial Statements Phase C Mock-first Hook

Completed:

* Added `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER`, default off.
* Added mockable fallback stub for A-share financial statements.
* Added fallback eligibility helper:
  * Allows confirmed A-share stocks.
  * Refuses indexes, ETFs, US, HK, ambiguous symbols, and Chinese names.
* Added primary result trigger helper:
  * Fallback only after missing/error/empty/unavailable primary financial data.
* Integrated fallback hook after the existing primary `get_financial_statements` path.
* Added unittest coverage and regression validation.

Not changed:

* No live `a-stock-data` call.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No dependency installation.
* No vendor code committed.

Next roadmap item:

Design a controlled live smoke test. Do not run it until the user confirms.

## 2026-07-09 a-stock-data Controlled Live Smoke Test Design

Completed:

* Read the current mock-first fallback hook and normalizer.
* Read the upstream readonly `a-stock-data` clone.
* Identified `sina_financial_report(code, report_type, num)` as the recommended first candidate.
* Added `docs_local/A_STOCK_DATA_LIVE_SMOKE_TEST_PLAN.md`.
* Recommended Option A: one-off external smoke script outside AgentLoop and outside `get_financial_statements`.

Not changed:

* No business code.
* No live request.
* No dependency installation.
* No provider-chain or loader changes.
* No Web UI changes.

Next roadmap item:

After user approval, implement the one-off smoke script and keep outputs in ignored `local_reports`.

## 2026-07-09 a-stock-data One-off Financial Live Smoke

Completed:

* Added `scripts/smoke_a_stock_data_financials.py`.
* Ran a controlled live smoke for:
  * `600519.SH income`
  * `300750.SZ income`
* Both returned 3 rows.
* Both included `报告期`.
* Both normalized successfully with latest detected date `2026-03-31`.

Not changed:

* No AgentLoop integration.
* No official fallback hook live implementation.
* No provider-chain or loader changes.
* No Web UI changes.
* No dependency installation.

Next roadmap item:

Decide whether to implement live fetch behind `fetch_a_stock_financials(...)`, still feature-flagged and default off.

## 2026-07-09 a-stock-data Balance/Cashflow Follow-up Smoke

Completed:

* Ran the existing one-off smoke script for balance and cash-flow statements.
* Validated both `600519.SH` and `300750.SZ`.
* All four calls returned 3 rows.
* All four included `报告期`.
* All four normalized successfully with latest detected date `2026-03-31`.

Next roadmap item:

Design live fetch implementation behind `fetch_a_stock_financials(...)` for `income`, `balance`, and `cashflow`, feature-flagged and default off.

## 2026-07-09 a-stock-data Phase D Live Fetch Behind Flag

Completed:

* Implemented live Sina financial fetch behind `fetch_a_stock_financials(...)`.
* Supported MVP statement mappings:
  * `income -> lrb`
  * `balance -> fzb`
  * `cashflow -> llb`
* Kept `indicators` out of scope.
* Kept `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` default off.
* Kept the official fallback hook fallback-only after primary failure or empty primary data.
* Ran direct function smoke for `600519.SH` and `300750.SZ`; all six symbol/statement combinations returned 3 rows with latest date `2026-03-31`.

Not changed:

* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No fund-flow, news, reports, or indicators adapter.

Next roadmap item:

Decide whether to run a controlled `get_financial_statements` fallback smoke with the feature flag on and primary provider failure simulated or forced in a narrow test harness. Do not run Web UI yet.

## 2026-07-09 a-stock-data Phase E Controlled Direct Tool Fallback Smoke

Completed:

* Added a direct smoke script for the official `get_financial_statements` tool path.
* Forced primary provider failure in-process instead of depending on real Eastmoney failure.
* Temporarily enabled `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1` only inside the script process.
* Verified live fallback succeeds for:
  * `600519.SH income`
  * `300750.SZ income`
  * `600519.SH balance`
  * `600519.SH cashflow`
* Verified fallback is refused for:
  * `510300.SH income`
  * `QQQ.US income`
  * `000001.SH income`

Not changed:

* No Web UI.
* No AgentLoop research task.
* No provider-chain changes.
* No loader changes.
* Feature flag remains default off.

Next roadmap item:

Back up the Phase E commit to the fork after user confirmation. Then decide whether the next validation should be a narrow API/tool smoke or whether to keep Web UI deferred until more data-quality metadata is added to financial statements.
