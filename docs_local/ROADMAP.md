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
* Default: off.
* Web UI retest after the expanded guard passed for `000001`, `贵州茅台`, `600519`, and `600519.SH`.
* Remaining before default-enable discussion: boundary Web UI retest for `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.
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

* Pre-tool Symbol Guard: candidate for default-on after user approval.
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
