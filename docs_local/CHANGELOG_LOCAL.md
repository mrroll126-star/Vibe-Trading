# Local Changelog

This changelog tracks local-only changes that are not part of upstream Vibe-Trading.

## 2026-07-05

### Added

- Cloned upstream `HKUDS/Vibe-Trading` into the local project workspace.
- Created local branch model:
  - `main`
  - `dev`
  - `feature/bootstrap-local-setup`
- Added `docs_local/` project management skeleton.

### Changed

- No upstream business code changed.

### Security

- No real `.env`, token, API key, OAuth file, cache, database, or log was created.
- No shell tools were enabled.
- No remote access was exposed.

### Git

- No commits created yet.
- No push performed.
- `origin` still points to upstream and should be changed after the user creates a fork.

## 2026-07-05 Read-Only Discovery Update

### Added

- Expanded `CURRENT_ARCHITECTURE.md` with runtime, entry points, data source layer, tool layer, API/security behavior, storage/cache locations, and known risks.
- Expanded `DATA_SOURCE_TEST_REPORT.md` with provider files, fallback chains, symbol formats, existing tests, and a future US smoke test proposal.
- Expanded `DEPLOYMENT_TAILSCALE.md` with a safe Tailnet-only access plan.
- Expanded `TEST_REPORT.md` with a next-round deployment plan, without running it.
- Updated `NEXT_TASKS.md` with the recommended next step.

### Changed

- Documentation only.

### Security

- No auth logic changed.
- No shell tools enabled.
- No `.env`, token, API key, OAuth file, cache, database, or log was created.
- No service was exposed.

## 2026-07-05 Basic Local Deployment

### Environment

- Installed Homebrew Python 3.11 because the machine only had system Python 3.9.6.
- Created project virtual environment at `.venv`.
- Installed backend dependencies with editable install.
- Installed frontend dependencies with npm.

### Validation

- Backend started successfully on `127.0.0.1:8899`.
- Frontend started successfully on `127.0.0.1:5899`.
- Verified backend health, API metadata, CLI help, frontend HTML, and local API access.
- Stopped both services after validation.

### Changed

- Documentation only.
- No `.gitignore` change was needed because `.venv/`, `node_modules/`, `agent/.env`, and `.env` were already ignored.

### Security

- No real `.env` was created.
- No token/API key/OAuth file was created.
- Shell tools were not enabled.
- Authentication logic was not changed.
- Services were bound only to `127.0.0.1` during testing.

## 2026-07-05 Deployment Stabilization

### Git

- Created local commit `a348b36 docs: record local deployment setup`.
- No push was performed.

### Added

- Added `docs_local/LOCAL_ENV_SETUP.md` with placeholder-only local LLM and API auth configuration guidance.

### Updated

- Updated Tailscale dry run plan with verified local ports and next test steps.
- Updated yfinance diagnostic notes.
- Updated US data-source smoke test readiness notes.

### Security

- No real `.env` was created.
- No token/API key/OAuth file was created.
- Shell tools remain disabled.
- No authentication logic was changed.
- No provider chain was changed.

## 2026-07-05 US Data Source Smoke Test

### Added

- Added `scripts/smoke_test_us_data_sources.py`, an independent diagnostic script for existing US data loaders.
- Added `local_reports/` to `.gitignore` so generated local JSON/Markdown reports are not committed.

### Updated

- Updated `DATA_SOURCE_TEST_REPORT.md` with implementation details and quick-run results.
- Updated `TEST_REPORT.md` with commands, results, failures, and rerun instructions.
- Updated `CODEX_WORKLOG.md`, `NEXT_TASKS.md`, and `CURRENT_ARCHITECTURE.md`.

### Validation

- Script syntax check passed.
- Quick smoke test completed successfully.
- Direct Yahoo, Sina, and Eastmoney returned AAPL/MSFT 1-month daily bars.

### Security

- No real `.env` was created.
- No token/API key/OAuth file was created.
- Missing API-key providers were skipped.
- Shell tools remain disabled.
- Authentication logic was not changed.
- Provider chain was not changed.

## 2026-07-05 Tailscale Runbook And API Auth Prep

### Added

- Added `docs_local/REMOTE_ACCESS_RUNBOOK.md` for future Tailnet startup and access.
- Created local ignored `agent/.env` with a generated `API_AUTH_KEY`.

### Updated

- Updated `DEPLOYMENT_TAILSCALE.md` with current Tailscale status and binding recommendations.
- Updated `TEST_REPORT.md` with Tailscale/environment checks.
- Updated `CODEX_WORKLOG.md`, `NEXT_TASKS.md`, and `CURRENT_ARCHITECTURE.md`.

### Validation

- Confirmed `agent/.env` is ignored by Git.
- Confirmed `agent/.env` contains `API_AUTH_KEY`.
- Confirmed `agent/.env` contains `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
- Confirmed Tailscale is not installed or not on `PATH`, so remote dry run was not executed.

### Security

- The full API auth key was not printed in documentation.
- No real LLM provider key was configured.
- No shell tools were enabled.
- No remote service was exposed.

## 2026-07-05 Web UI Product Smoke Test

### Added

- Added `docs_local/WEB_UI_SMOKE_TEST_REPORT.md`.
- Added `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`.

### Updated

- Updated Phase 0 summary with Web UI validation results.
- Updated roadmap and next tasks with A-share trading-day validation.
- Updated minimal research task notes with Web UI SPY.US and 600519.SH results.
- Updated test report and worklog.

### Validation

- Backend started on `127.0.0.1:8899`.
- Frontend started on `127.0.0.1:5899`.
- Web UI generated reports for `SPY.US` and `600519.SH`.
- Runtime page stayed read-only and did not start broker connectors.

### Security

- No real key was printed.
- `agent/.env` was not committed.
- Ignored run/session artifacts were not committed.
- Shell tools remained disabled.
- No provider chain was changed.
- No business code was modified.

## 2026-07-05 Trading-Day Readiness Tests

### Added

- Added `docs_local/PRODUCT_BACKLOG.md`.

### Updated

- Updated `DATA_SOURCE_TEST_REPORT.md` with full US smoke test results.
- Updated `A_SHARE_TRADING_DAY_TEST_PLAN.md` with preflight results and a real trading-day recording template.
- Updated `WEB_UI_SMOKE_TEST_REPORT.md` with CLI A-share preflight follow-up.
- Updated `TEST_REPORT.md`, `NEXT_TASKS.md`, and `CODEX_WORKLOG.md`.

### Validation

- Full US smoke test completed with explicit `.US` symbols.
- A-share lightweight OHLCV preflight completed for six symbols.
- A-share minimal research tasks completed for `600519.SH` and `300750.SZ`.

### Security

- No real key was printed.
- `agent/.env` was not committed.
- `local_reports/`, `agent/runs/`, and `agent/sessions/` were not committed.
- Shell tools remained disabled.
- No remote service was exposed.
- No business code was modified.

## 2026-07-05 Symbol Normalization Design

### Added

- Added `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`.
- Added `docs_local/SYMBOL_NORMALIZATION_ACCEPTANCE_TESTS.md`.

### Updated

- Updated `PRODUCT_BACKLOG.md` to mark Symbol Normalization as a Phase 1 foundation item.
- Updated `NEXT_TASKS.md`, `ROADMAP.md`, and `CODEX_WORKLOG.md`.

### Security / Boundary

- Documentation only.
- No business code was modified.
- No provider chain was changed.
- No `a-stock-data` integration was attempted.
- No ignored local runtime artifacts were committed.

## 2026-07-08 Web UI Pre-tool Symbol Guard Retest

### Updated

- Updated `WEB_UI_SMOKE_TEST_REPORT.md` with Web UI Pre-tool Symbol Guard retest results.
- Updated `TEST_REPORT.md` with commands, prompts, session IDs, run IDs, and trace findings.
- Updated `PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md` with Phase D Web UI retest findings.
- Updated `PRODUCT_BACKLOG.md` with the remaining gap: non-market-data tools are not yet guarded for ambiguous/name-based symbol intent.
- Updated `NEXT_TASKS.md` to prioritize extending guard coverage before default-enabling symbol flags.
- Updated `CODEX_WORKLOG.md` with this retest action.

### Validation

- Backend started locally with:
  - `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`
  - `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`
- Frontend started locally on `127.0.0.1:5899`.
- Web UI prompts were submitted for `600519`, `QQQ`, `00700`, `000001`, `贵州茅台`, and `600519.SH`.
- Local session traces confirmed `get_market_data` was blocked for `000001` and `贵州茅台`.

### Result

- Partial pass.
- Safe bare symbols were allowed.
- Explicit symbols were allowed.
- Ambiguous/name-based market-data calls were blocked.
- Non-market-data stock tools still ran for ambiguous/name-based prompts, so the flags should remain off by default.

### Security

- No real key was printed.
- `agent/.env` was not committed.
- `agent/runs/` and `agent/sessions/` were not committed.
- Shell tools remained disabled.
- Services were bound only to `127.0.0.1`.
- No provider chain was changed.
- No business code was modified.

## 2026-07-08 Extend Pre-tool Symbol Guard To Stock Tools

### Changed

- Extended `agent/src/symbols/intent_guard.py` from `get_market_data` only to the first batch of stock-specific tools.
- Updated AgentLoop guard integration to use the shared guarded-tool list.
- Added tests for `get_fund_flow`, `get_stock_news`, `get_research_reports`, and `get_sector_info`.

### Covered Tools

- `get_market_data`
- `get_fund_flow`
- `get_stock_news`
- `get_research_reports`
- `get_sector_info`

### Not Covered

- `web_search`
- `read_url`
- `search_symbol`
- `read_document`

### Validation

- Symbol test suite passed: 68 tests.
- Anti-hallucination regression suite passed: 46 tests.
- Compile check passed.
- Lightweight mock validation confirmed clarify/block paths do not call providers.

### Security / Boundary

- Feature flag remains off by default.
- No Web UI retest was run.
- No provider chain was changed.
- No loader was changed.
- No `a-stock-data` integration was attempted.
- No remote service was exposed.
- Shell tools remained disabled.

## 2026-07-08 Web UI Stock-specific Symbol Guard Retest

### Updated

- Updated `WEB_UI_SMOKE_TEST_REPORT.md` with the real Web UI retest results.
- Updated `TEST_REPORT.md` with sessions, run IDs, guard evidence, and service shutdown status.
- Updated `PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md` with Phase F retest conclusions.
- Updated `PRODUCT_BACKLOG.md`, `NEXT_TASKS.md`, `CODEX_WORKLOG.md`, and `ROADMAP.md`.

### Validation

- Backend started locally with both symbol feature flags enabled for the test run only.
- Frontend started locally on `127.0.0.1:5899`.
- Web UI prompts were submitted for `000001`, `贵州茅台`, `600519`, and `600519.SH`.
- Local traces confirmed `000001` and `贵州茅台` did not call first-batch stock-specific providers before clarification.

### Result

- Web UI stock-specific symbol guard retest passed.
- `600519` and `600519.SH` remained allowed.
- Feature flags remain off by default pending a boundary retest.

### Security / Boundary

- No real key was printed.
- `agent/.env` was not committed.
- `agent/runs/` and `agent/sessions/` were not committed.
- Shell tools remained disabled.
- Services were bound only to `127.0.0.1`.
- No provider chain was changed.
- No business code was modified.

## 2026-07-05 Symbol Normalizer Helper

### Added

- Added `agent/src/symbols/__init__.py`.
- Added `agent/src/symbols/normalizer.py`.
- Added `agent/tests/test_symbol_normalizer.py`.

### Updated

- Updated symbol normalization design and acceptance-test docs with implementation status.
- Updated `TEST_REPORT.md`, `CODEX_WORKLOG.md`, `NEXT_TASKS.md`, and `PRODUCT_BACKLOG.md`.

### Validation

- `pytest` was not available in the current `.venv`.
- Ran `.venv/bin/python -m unittest agent.tests.test_symbol_normalizer`.
- Result: 12 tests passed.

### Boundary

- No existing tool behavior changed.
- No provider chain changed.
- No Web UI changed.
- No network/data-source calls added.
- No authentication logic was changed.
- `agent/.env` remains untracked and must not be committed.

## 2026-07-05 Closeout And LLM Provider Prep

### Updated

- Marked Tailscale dry run as deferred.
- Documented that the user is keeping the Mac App Store Tailscale variant because existing virtual domains and other projects depend on it.
- Updated `LOCAL_ENV_SETUP.md` with provider names, exact environment variables, and safe editing steps.
- Added `MINIMAL_RESEARCH_TASK.md` for the first approved post-LLM validation.
- Reordered `NEXT_TASKS.md` around proving the original Agent workflow before adding new data-source integrations.

### Security

- No real LLM provider key was configured.
- Existing `API_AUTH_KEY` in `agent/.env` was not changed.
- Shell tools remain disabled.
- No remote Web UI exposure was attempted.
- No business code was changed.

## 2026-07-05 DeepSeek Minimal Research Verification

### Validation

- Verified DeepSeek provider configuration from ignored `agent/.env`.
- Ran provider doctor with redacted output.
- Ran direct hello and JSON-output tests.
- Started backend and frontend locally.
- Ran one minimal SPY research task.

### Result

- DeepSeek `deepseek-v4-pro` is usable in this local setup.
- The original Vibe-Trading Agent workflow completed a minimal research task.
- Run output is stored under ignored `agent/runs/20260705_162441_99_2b6f81`.

### Notes

- Some data-tool calls failed because the prompt used bare `SPY`; next prompt should use `SPY.US`.
- Yahoo/yfinance network/TLS issues remain.

### Security

- No full API key was printed.
- `agent/.env` was not committed.
- Shell tools remained disabled.
- No remote access was exposed.
- No business code was changed.

## 2026-07-05 Phase 0 Closeout

### Added

- Added `docs_local/PHASE_0_BOOTSTRAP_SUMMARY.md`.
- Added `docs_local/PHASE_1_PLAN.md`.

### Updated

- Updated `ROADMAP.md` to mark Phase 0 complete and link Phase 1.
- Updated `NEXT_TASKS.md` with the recommended Phase 1 sequence.
- Updated `CODEX_WORKLOG.md`.
- Updated `MINIMAL_RESEARCH_TASK.md` with Phase 0 conclusion.

### Security

- No `agent/.env` commit.
- No `agent/runs/` commit.
- No business code changes.
- No provider chain changes.
- No new remote exposure.

## 2026-07-05 Symbol Normalizer Integration Plan

### Added

- Added `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.

### Updated

- Updated `ROADMAP.md`.
- Updated `NEXT_TASKS.md`.
- Updated `PRODUCT_BACKLOG.md`.
- Updated `CODEX_WORKLOG.md`.
- Updated `SYMBOL_NORMALIZATION_DESIGN.md`.

### Decision

- Do not connect the normalizer broadly yet.
- Recommended first integration, if later approved: `get_market_data` only.
- Recommended feature flag: `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0` for first integration.

### Boundary

- No business code changes.
- No provider-chain changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No ignored runtime or secret files committed.

## 2026-07-05 DeepSeek v4-flash Model Switch Test

### Updated

- Updated ignored local `agent/.env` model setting from `deepseek-v4-pro` to `deepseek-v4-flash`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/LLM_PROVIDER_STRATEGY.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.

### Validation

- `vibe-trading provider doctor` succeeded with `deepseek-v4-flash`.
- Minimal hello test succeeded with `deepseek-v4-flash`.
- No additional DeepSeek key was required in this local test.

### Boundary

- `agent/.env` remains ignored and must not be committed.
- No full API key was printed.
- No backend restart.
- No real research task.
- No business code changes.

## 2026-07-06 Data Freshness & Anti-Hallucination Guardrails Design

### Added

- Added `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
- Added ADR for “LLM must not invent market data”.

### Updated

- Updated `docs_local/ARCHITECTURE_DECISIONS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/ROADMAP.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/PHASE_1_PLAN.md`.
- Updated `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`.

### Decision

- Data Freshness & Anti-Hallucination Guardrails are now a high-priority Phase 1 safety foundation.
- Guardrails must be implemented before `a-stock-data` is integrated into production research workflows.
- Reports should separate data facts, model interpretation, missing data, source failures, assumptions, and not-investment-advice boundaries.

### Boundary

- No business code changes.
- No provider-chain changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No real research task.
- No ignored runtime or secret files committed.

## 2026-07-07 get_market_data Freshness Wrapper MVP

### Added

- Added `agent/src/data_quality/__init__.py`.
- Added `agent/src/data_quality/freshness.py`.
- Added `agent/tests/test_data_freshness.py`.

### Updated

- Updated `agent/src/market_data.py` to append per-symbol freshness metadata under `_data_quality`.
- Updated `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.

### Validation

- `.venv/bin/python -m unittest agent.tests.test_data_freshness` passed with 8 tests.
- Compile check passed.
- Direct `fetch_market_data_json` validation passed.
- Existing pytest regression command could not run because `pytest` is not installed in the current virtual environment.

### Boundary

- No provider-chain changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No real research task.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Source Summary In Reports MVP

### Added

- Added `agent/src/data_quality/report_summary.py`.
- Added `agent/tests/test_report_data_source_summary.py`.

### Updated

- Updated `agent/src/data_quality/__init__.py`.
- Updated `agent/src/agent/loop.py` to collect `get_market_data` `_data_quality` and append a report audit section.
- Updated `agent/src/agent/context.py` with data truthfulness rules.
- Updated `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.

### Validation

- `.venv/bin/python -m unittest agent.tests.test_data_freshness` passed with 8 tests.
- `.venv/bin/python -m unittest agent.tests.test_report_data_source_summary` passed with 8 tests.
- `.venv/bin/python -m compileall -q agent/src agent/tests` passed.
- Mock `append_data_source_summary` validation passed.

### Boundary

- Only `get_market_data` `_data_quality` is surfaced.
- No hard report gate.
- No provider-chain changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No real research task.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Time-sensitive Report Gate MVP

### Added

- Added `agent/src/data_quality/report_gate.py`.
- Added `agent/tests/test_report_gate.py`.

### Updated

- Updated `agent/src/data_quality/__init__.py`.
- Updated `agent/src/agent/loop.py` to apply the report gate before final content is persisted.
- Updated `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.

### Validation

- `.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate` passed with 29 tests.
- `.venv/bin/python -m compileall -q agent/src agent/tests` passed.
- Mock report-gate validation passed.

### Boundary

- Gate uses only `get_market_data` `_data_quality`.
- No provider-chain changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No real research task.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Extended Data Quality Contract + No Estimate Guard MVP

### Added

- Added generic `DataQualityMetadata` helpers for selected non-market-data tools.
- Added `agent/src/data_quality/no_estimate.py`.
- Added `agent/tests/test_extended_data_quality.py`.
- Added `agent/tests/test_no_estimate_guard.py`.

### Updated

- Updated `agent/src/data_quality/freshness.py` to assess `get_fund_flow`, `get_stock_news`, and `get_research_reports`.
- Updated `agent/src/tools/fund_flow_tool.py` to append per-symbol `_data_quality`.
- Updated `agent/src/tools/stock_news_tool.py` to append `_data_quality` for articles/matches and supported errors.
- Updated `agent/src/tools/research_reports_tool.py` to append `_data_quality` for reports and supported errors.
- Updated `agent/src/data_quality/report_summary.py` to group Source Summary by tool.
- Updated `agent/src/agent/context.py` with conditional no-estimate system prompt guidance.
- Updated `agent/src/agent/loop.py` to capture general `_data_quality` and append No Estimate Warning when needed.
- Updated `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.

### Validation

- `.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard` passed with 46 tests.
- `.venv/bin/python -m compileall -q agent/src agent/tests` passed.
- Mock validation passed.

### Boundary

- No provider-chain changes.
- No loader changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No full research task.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Web UI Red-Light Prompt Retest

### Updated

- Updated `docs_local/WEB_UI_SMOKE_TEST_REPORT.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.

### Validation

- Real Web UI prompt submitted through `http://127.0.0.1:5899/agent`.
- Backend served on `127.0.0.1:8899`.
- Web session: `57a481605851`.
- Run ID: `20260707_173205_10_7f61dd`.
- Final report included Data Source Summary, Missing Data, Source Warnings, and No Estimate Warning.

### Boundary

- No business code changes in this retest round.
- No provider-chain changes.
- No Web UI code changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Symbol Normalizer Feature-Flagged `get_market_data` Integration

### Added

- Added `agent/src/symbols/config.py`.
- Added `agent/tests/test_market_data_symbol_normalization.py`.

### Updated

- Updated `agent/src/market_data.py` to normalize `get_market_data` inputs only when `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` is enabled.
- Updated `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/ROADMAP.md`.

### Validation

- `.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization` passed with 23 tests.
- `.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard` passed with 46 tests.
- `.venv/bin/python -m compileall -q agent/src agent/tests` passed.
- Direct mock validation passed.

### Boundary

- Feature flag default is off.
- Only `get_market_data` is integrated.
- No provider-chain changes.
- No loader changes.
- No Web UI changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-07 Web UI Bare Symbol Retest

### Updated

- Updated `docs_local/WEB_UI_SMOKE_TEST_REPORT.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/ROADMAP.md`.

### Findings

- `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1` was tested through the Web UI.
- `_symbol_normalization` and `_data_quality` both appeared in `get_market_data` results.
- `Data Source Summary` appeared in final reports.
- The Web UI Agent path may normalize or guess symbols before `get_market_data` receives the original user input.
- Ambiguous `000001` and Chinese name `贵州茅台` should not be considered safe for default-enable behavior yet.

### Boundary

- No business code changes.
- No provider-chain changes.
- No Web UI code changes.
- No `a-stock-data` integration.
- No yfinance fix.
- No sensitive or runtime files committed.

## 2026-07-08 Pre-tool Symbol Intent Guard Design

### Added

- Added `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`.

### Updated

- Updated `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/ROADMAP.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/TEST_REPORT.md`.

### Findings

- The original user prompt is available before tool execution.
- Tool name and arguments are available before execution.
- `_invoke_tool` is the shared executor, but it currently does not receive original prompt context.
- The lowest-risk design is a feature-flagged AgentLoop guard before `get_market_data` provider execution.

### Boundary

- Design-only round.
- No business code changes.
- No provider-chain changes.
- No Web UI changes.
- No service startup.
- No `a-stock-data` integration.
- No sensitive or runtime files committed.

## 2026-07-08 Pure Pre-tool Symbol Intent Guard Function

### Added

- Added `agent/src/symbols/intent_guard.py`.
- Added `agent/tests/test_symbol_intent_guard.py`.

### Updated

- Updated `agent/src/symbols/__init__.py`.
- Updated `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/ROADMAP.md`.

### Validation

- Symbol-related unittest command passed with 43 tests.
- Anti-hallucination regression unittest command passed with 46 tests.
- Compile check passed.
- Lightweight pure-function validation passed.

### Boundary

- Pure function only.
- No AgentLoop integration.
- No tool execution changes.
- No provider-chain changes.
- No Web UI changes.
- No service startup.
- No `a-stock-data` integration.
- No sensitive or runtime files committed.

## 2026-07-08 Feature-flagged AgentLoop Pre-tool Symbol Guard

### Added

- Added `is_pre_tool_symbol_guard_enabled()` in `agent/src/symbols/config.py`.
- Added `agent/tests/test_symbol_intent_guard_integration.py`.

### Updated

- Updated `agent/src/agent/loop.py`.
- Updated `agent/src/agent/context.py`.
- Updated `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZATION_DESIGN.md`.
- Updated `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`.
- Updated `docs_local/TEST_REPORT.md`.
- Updated `docs_local/CODEX_WORKLOG.md`.
- Updated `docs_local/CHANGELOG_LOCAL.md`.
- Updated `docs_local/NEXT_TASKS.md`.
- Updated `docs_local/PRODUCT_BACKLOG.md`.
- Updated `docs_local/ROADMAP.md`.

### Validation

- AgentLoop guard integration tests passed with 10 tests.
- Symbol-related tests passed with 43 tests.
- Anti-hallucination regression tests passed with 46 tests.
- Compile check passed.
- Lightweight mock validation passed.

### Boundary

- Feature flag default is off.
- Only `get_market_data` is guarded.
- Guarded `clarify` / `block` does not call providers.
- No provider-chain changes.
- No loader changes.
- No Web UI code changes.
- No service startup.
- No `a-stock-data` integration.
- No sensitive or runtime files committed.
## 2026-07-08

### Documentation

Recorded Web UI boundary retest for the stock-specific symbol guard:

* `QQQ` safe bare ticker passed.
* `00700` safe bare HK code passed.
* `000001.SZ` explicit A-share stock passed and freshness gate blocked stale current-day market analysis.
* `000001.SH` explicit A-share index market-data path passed, with an asset-type-aware routing backlog item.

### Boundary

* Documentation-only update.
* No business code changes.
* No provider-chain changes.
* No default feature flag changes.
* No sensitive files committed.

### Added

* `docs_local/ASSET_TYPE_AWARE_TOOL_ROUTING_DESIGN.md`

### Updated

* Documented that `000001.SH` exposes an index / stock-tool routing issue.
* Clarified that Pre-tool Symbol Guard is a default-on candidate, but asset-type routing should be designed first.
* Clarified that Symbol Normalizer should remain feature-flagged.
* Kept `a-stock-data` downstream.

### Added

* `agent/src/tools/routing_guard.py`
* `agent/tests/test_tool_routing_guard.py`

### Validation

* Pure routing guard unit tests passed with 27 tests.
* Symbol-related regression tests passed with 68 tests.
* Anti-hallucination regression tests passed with 46 tests.
* Compile check passed.

### Boundary

* Pure function only.
* No AgentLoop integration.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.

### Added

* Feature flag `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD`.
* AgentLoop integration for asset-type routing guard.
* `agent/tests/test_tool_routing_guard_integration.py`.

### Behavior

* Default off.
* `block` / `ask_for_confirmation` stop provider calls.
* `warn` allows provider calls and appends `_tool_routing_guard`.
* Pre-tool Symbol Intent Guard still runs first.

### Validation

* Routing guard + integration tests passed with 43 tests.
* Symbol regression tests passed with 68 tests.
* Anti-hallucination regression tests passed with 46 tests.
* Compile check passed.

## 2026-07-08

### Fixed

* Applied Asset-type Routing Guard to parallel readonly tool execution in `AgentLoop._execute_parallel`.
* Preserved Pre-tool Symbol Intent Guard priority before asset-type routing.
* Added market-wide sector mode allowance for `get_sector_info(mode=ranking|list|overview)` without a single symbol.

### Added

* Parallel-path tests for asset routing block, warn, flag-off behavior, non-covered tools, symbol-guard precedence, and market-wide sector ranking.

### Validation

* Routing guard tests passed with 53 tests.
* Symbol regression tests passed with 68 tests.
* Anti-hallucination regression tests passed with 46 tests.
* Compile check passed.

### Boundary

* Feature flag remains default off.
* No provider-chain changes.
* No loader changes.
* No Web UI code changes.
* No `a-stock-data` integration.
* No sensitive/runtime files committed.

## 2026-07-08

### Fixed

* Allowed market-wide `get_stock_news` calls through Pre-tool Symbol Intent Guard when no single symbol is required.
* Preserved guard behavior for symbol-specific `get_stock_news` calls.

### Added

* Unit tests for `get_stock_news(scope/mode=global|market|all|sector)`.
* Integration tests for parallel market-wide news allow and symbol-specific news clarify.

### Validation

* Symbol regression tests passed with 83 tests.
* Routing regression tests passed with 53 tests.
* Anti-hallucination regression tests passed with 46 tests.
* Compile check passed.

### Boundary

* No provider-chain changes.
* No loader changes.
* No Web UI code changes.
* No `a-stock-data` integration.
* No sensitive/runtime files committed.
