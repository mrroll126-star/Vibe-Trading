# Next Tasks

Status: Phase 0 completed. Phase 1 foundation work is in progress.

Basic local deployment works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable
* DeepSeek provider: verified
* Current local DeepSeek model: `deepseek-v4-flash`
* Minimal native Agent research task: completed

## Priority Rule

Data Freshness & Anti-Hallucination Guardrails have higher priority than data-source expansion.

Reason:

* Adding more data sources does not solve hallucination by itself.
* If the LLM can still invent today's close, volume, turnover, fund flow, news, or financial metrics when data is missing, the product remains risky.
* Every future provider, including `a-stock-data`, should follow a freshness and source-failure contract.

Highest principle:

* LLM must not invent market data.

## Current Recommended Order After Extended Guardrail MVP

1. **Web UI bare-symbol retest with Symbol Normalizer enabled manually**
   * Business value: verifies that `600519`, `QQQ`, and `00700` can work through the real Agent/Web UI path when `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`.
   * Risk: consumes a small amount of LLM tokens and may expose prompt/tool-routing issues unrelated to the helper.
   * Boundary: test only; do not enable the flag by default.

2. **Decide whether to default-enable Symbol Normalizer later**
   * Business value: determines whether natural symbols should become normal product behavior.
   * Risk: ambiguous symbols such as `000001` can still require confirmation.
   * Boundary: decide from test evidence, not assumption.

3. **Optional stricter No Estimate Guard**
   * Business value: prevents estimated market-fact phrases from remaining in the main report body when the user explicitly says no estimates.
   * Risk: automatic rewrite can overcorrect or remove useful context.
   * Boundary: design first; consider block/rewrite only for explicit no-estimate prompts.

4. **`a-stock-data` adapter planning**
   * Business value: prepares richer A-share data after guardrails exist.
   * Risk: adding data sources before contracts are complete can hide failures.
   * Boundary: planning first; no provider replacement.

5. **Extend data quality to remaining A-share tools**
   * Business value: brings northbound flow, margin trading, shareholder count, sector info, and financial statements into the same audit model.
   * Risk: each tool has a different date/error shape.
   * Boundary: continue additive `_data_quality` only.

## Completed Phase 1 Validation: Web UI Red-Light Prompt Retest

Status: completed on 2026-07-07.

Result:

* Web session: `57a481605851`.
* Run ID: `20260707_173205_10_7f61dd`.
* Data Source Summary appeared in the final Web UI report.
* `get_market_data`, `get_fund_flow`, and `get_stock_news` appeared.
* `get_stock_news` stale status was disclosed.
* No Estimate Warning appeared.
* Main body still contained estimated market-fact phrasing, which is expected for the warning-only MVP.

## Completed Phase 1 Item: Symbol Normalizer `get_market_data` Integration

Status: completed on 2026-07-07.

Implemented:

* `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` feature flag.
* Default off behavior.
* `get_market_data` entry-point normalization.
* `_symbol_normalization` metadata.
* Preservation of `_data_quality`.
* Tests for flag off/on and A-share, US, HK, ambiguous, Chinese, invalid, multi-symbol cases.

Remaining gap:

* No Web UI bare-symbol retest yet.
* No integration for `get_stock_news`, `get_fund_flow`, or `get_research_reports`.
* Not approved to default-enable yet.

## Recommended Task 1: A-Share Trading-Day Real Usage Test

Priority: high.

Business value:

* Confirms whether the original Vibe-Trading A-share workflow is useful on a real trading day.
* Captures data freshness, report quality, missing-field gaps, and hallucination risk before code changes.
* Produces evidence for whether `a-stock-data` is needed and where.

Extra records to capture:

* Whether current-day data was retrieved.
* Data timestamp or data date.
* Which providers succeeded or failed.
* Whether the report disclosed missing data.
* Whether the report made factual claims without returned data.

See:

* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`

Boundary:

* Test only.
* Do not ask for buy/sell advice.
* Do not integrate new providers.
* Keep shell tools disabled.

## Completed Phase 1 Item: Source Summary In Reports MVP

Status: completed on 2026-07-07.

Implemented:

* `agent/src/data_quality/report_summary.py`
* Mechanical Data Source Summary / Missing Data / Source Warnings appendix.
* Agent loop capture of `get_market_data` `_data_quality`.
* System prompt data truthfulness rules.
* `agent/tests/test_report_data_source_summary.py`

Remaining gap:

* This is not a hard report gate.
* Only `get_market_data` `_data_quality` is covered.
* Other tools such as `fund_flow`, `news`, and `research_reports` are not covered yet.

## Completed Phase 1 Item: Time-sensitive Report Gate MVP

Status: completed on 2026-07-07.

Implemented:

* `agent/src/data_quality/report_gate.py`
* Time-sensitive keyword detection.
* Blocking for `stale`, `missing`, and `unknown` `get_market_data` freshness.
* Blocking for explicit close / closing price prompts when daily close is warned as not official close.
* Deterministic `Data Insufficient Report`.
* `agent/tests/test_report_gate.py`.

Remaining gap:

* Only `get_market_data` `_data_quality` is gated.
* `fund_flow`, `news`, `research_reports`, announcements, and financials are not gated yet.
* If no `get_market_data` `_data_quality` exists, the MVP does not block.

## Completed Phase 1 Item: Extended Data Quality Contract + No Estimate Guard MVP

Status: completed on 2026-07-07.

Implemented:

* `_data_quality` metadata for `get_fund_flow`, `get_stock_news`, and `get_research_reports`.
* Multi-tool Source Summary grouping.
* Rule-based No Estimate Guard for explicit no-estimate prompts.
* `agent/tests/test_extended_data_quality.py`.
* `agent/tests/test_no_estimate_guard.py`.

Remaining gap:

* No Estimate Guard appends warning only; it does not rewrite the report body.
* Hard Data Insufficient Report gate still uses only `get_market_data`.
* Remaining A-share tools still need metadata later.

## Recommended Task 2: Symbol Normalizer `get_market_data` Integration

Priority: medium-high.

Business value:

* Helps natural inputs like `600519`, `QQQ`, and `00700`.
* Freshness and gate infrastructure now provides a safer audit layer for normalized symbol outputs.

Boundary:

* Feature flag recommended.
* Start with `get_market_data` only.
* Do not broadly connect all tools.

## Completed Phase 1 Item: `get_market_data` Freshness Wrapper MVP

Status: completed on 2026-07-07.

Implemented:

* `agent/src/data_quality/freshness.py`
* `_data_quality` metadata in `agent/src/market_data.py`
* `agent/tests/test_data_freshness.py`

Validation:

* Unittest passed with 8 tests.
* Direct validation confirmed original per-symbol data is preserved.

Remaining gap:

* Reports do not yet consistently surface or obey `_data_quality`.

## Recommended Task 4: Source Summary In Reports

Priority: high.

Business value:

* Ensures provider failures are visible to the user, not hidden only in trace.
* Adds report sections such as Data Source Summary, Missing Data, and Source Failures.
* Reduces risk that the LLM turns missing data into a normal-looking conclusion.

Boundary:

* Start with report structure and prompt/gate behavior.
* Do not rewrite the entire Web UI.

## Recommended Task 5: Symbol Normalizer `get_market_data` Integration

Priority: medium-high.

Business value:

* Helps natural inputs like `600519`, `QQQ`, and `00700`.
* Should be integrated after freshness wrapper design so normalized symbols carry `raw_input` and warnings into the data contract.

Current files:

* `agent/src/symbols/normalizer.py`
* `agent/tests/test_symbol_normalizer.py`
* `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`

Boundary:

* Feature flag recommended.
* Start with `get_market_data` only.
* Do not broadly connect all tools.

## Recommended Task 6: `a-stock-data` Adapter Planning

Priority: medium-high, but after freshness guardrails.

Business value:

* Enhances A-share datasets where existing providers are weak.
* Should be planned from real trading-day gaps.

Boundary:

* Planning only unless separately approved.
* Do not replace original providers.
* Any adapter must follow the freshness contract before production research use.

## Deferred / Later

### Custom Provider Plugin Framework Design

Priority: medium.

Why later:

* Useful for maintainability, but freshness guardrails define the contract custom providers must satisfy.

### LLM Router Design

Priority: medium.

Why later:

* Important for cost and quality, but does not directly prevent data hallucination.

### Reports Loading / Runs Unknown

Priority: medium.

Why later:

* Product usability issue, but not the highest factual-risk item unless it blocks auditability.

### yfinance TLS Fix

Priority: low-medium.

Why later:

* Important for US/HK profile paths, but source failure disclosure is needed before fixing one provider.

### Tailscale Web Dry Run

Status: deferred by user decision.

Current remote-control path:

* Remote desktop tool.

Future re-enable conditions:

* Tailnet-only.
* `API_AUTH_KEY`.
* Shell tools disabled.
* No public exposure.
* No `agent/.env` commit.

## Not Approved Yet

* Do not integrate `a-stock-data`.
* Do not replace provider fallback chains.
* Do not enable shell tools.
* Do not expose services remotely.
* Do not develop trading execution features.

## Current Recommended Order After Web UI Bare Symbol Retest

1. **Design pre-tool symbol intent guard**
   * Reason: Web UI retest showed the LLM can convert `000001` to `000001.SZ` and `贵州茅台` to `600519.SH` before `get_market_data` sees the raw input.
   * Business value: prevents silent misidentification in natural-language research tasks.
   * Risk: must be scoped carefully so explicit symbols like `600519.SH` continue to work.

2. **Keep Symbol Normalizer feature flag off by default**
   * Reason: direct helper tests pass, but real Web UI ambiguous/name handling is not safe enough for default enablement.
   * Business value: preserves stable explicit-symbol workflows while allowing controlled tests.

3. **Consider a small `get_market_data` hardening pass**
   * Reason: if a normalized result has `needs_confirmation=true`, final reports should surface that warning more prominently.
   * Business value: improves auditability without changing provider chains.

4. **Then revisit broader Symbol Normalizer rollout**
   * Reason: only after raw-input ambiguity is controlled should normalization expand to more tools.

5. **Keep `a-stock-data` adapter planning deferred**
   * Reason: input identity and data-quality contracts should stay ahead of new data-source integration.

## Current Recommended Order After Guard Design

1. **Implement pure pre-tool symbol guard function + tests**
   * Scope: no AgentLoop integration yet.
   * Value: prove the guard rules for `600519`, `QQQ`, `00700`, `000001`, `贵州茅台`, and wrong-symbol cases.

2. **Feature-flagged AgentLoop integration**
   * Scope: only `get_market_data`.
   * Flag: `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`.
   * Value: stop ambiguous or untraceable tool calls before provider execution.

3. **Web UI retest**
   * Scope: `600519`, `QQQ`, `00700`, `000001`, `贵州茅台`.
   * Value: confirm safe bare symbols pass and ambiguous/name inputs require clarification.

4. **Only then decide whether Symbol Normalizer can default on**
   * Current recommendation: keep default off.

5. **Keep `a-stock-data` adapter deferred**
   * Reason: symbol identity must be auditable before adding new A-share data sources.

## Current Recommended Order After Pure Guard Function

1. **Feature-flagged AgentLoop integration**
   * Scope: only intercept `get_market_data`.
   * Flag: `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`.
   * Default: off.

2. **Web UI retest**
   * Test `000001`, `贵州茅台`, `600519`, `QQQ`, and `00700`.
   * Expected: ambiguous/name inputs clarify; safe bare symbols pass.

3. **Default-enable decision**
   * Only consider enabling Symbol Normalizer by default after guard integration and Web UI retest pass.

4. **Keep `a-stock-data` deferred**
   * Reason: new data sources should come after symbol identity is auditable.

## Current Recommended Order After AgentLoop Guard Integration

1. **Web UI retest pre-tool guard**
   * Enable `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`.
   * Test `000001`, `贵州茅台`, `600519`, `QQQ`, and `00700`.

2. **Default-enable decision**
   * Decide whether the pre-tool guard and/or Symbol Normalizer can be enabled by default.
   * Current recommendation: keep defaults off until Web UI retest passes.

3. **`a-stock-data` adapter planning**
   * Still deferred until symbol identity and freshness contracts are stable.
