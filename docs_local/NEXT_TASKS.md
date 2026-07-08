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

## Current Recommended Order After Web UI Pre-tool Guard Retest

1. **Boundary Web UI retest before default-enable decision**
   * Business value: verifies safe US/HK bare symbols and explicit ambiguous symbols before making a product default decision.
   * Suggested cases: `QQQ`, `00700`, `000001.SZ`, `000001.SH`.
   * Risk: consumes LLM tokens and may expose unrelated tool-routing behavior.
   * Boundary: localhost only; shell tools disabled.

2. **Decide whether to default-enable Symbol Normalizer and Pre-tool Guard later**
   * Business value: determines whether natural symbols can become normal product behavior.
   * Risk: must wait for a full Web UI pass after the expanded guard.
   * Boundary: decide from a full pass, not from the current partial pass.

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

## Completed Phase 1 Validation: Web UI Pre-tool Symbol Guard Retest

Status: completed on 2026-07-08.

Flags used for this local run:

* `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`
* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`

Result:

* `600519`, `QQQ`, `00700`, and explicit `600519.SH` were not incorrectly blocked.
* `get_market_data` was guarded correctly for `000001` and `贵州茅台`.
* `000001` final answer asked the user to choose `000001.SZ` or `000001.SH`.
* `贵州茅台` final answer asked the user to confirm `600519.SH`.
* `_data_quality` remained present for allowed `get_market_data` calls.

Important gap:

* The guard currently covers `get_market_data` only.
* In the Web UI retest, `000001` still triggered `get_fund_flow`, `get_stock_news`, and `get_sector_info` with `000001.SZ`.
* `贵州茅台` still triggered `get_stock_news` and `get_sector_info` with `600519.SH`.
* Therefore, the current status is partial pass, not enough to default-enable the feature flags.

## Completed Phase 1 Item: Extended Pre-tool Guard To Stock-specific Tools

Status: completed on 2026-07-08.

Implemented:

* Guarded tool list now includes:
  * `get_market_data`
  * `get_fund_flow`
  * `get_stock_news`
  * `get_research_reports`
  * `get_sector_info`
* Feature flag remains `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`.
* Default remains off.
* `web_search`, `read_url`, `search_symbol`, and `read_document` are not covered by this MVP.

Validation:

* Symbol tests passed.
* Anti-hallucination regression tests passed.
* Compile check passed.
* Lightweight mock validation passed.

Remaining gap:

* Web UI retest passed for `000001`, `贵州茅台`, `600519`, and `600519.SH`.
* Do not default-enable Symbol Normalizer or Pre-tool Guard until a boundary retest also covers `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.

## Completed Phase 1 Validation: Web UI Stock-specific Guard Retest

Status: completed on 2026-07-08.

Result:

* `000001`: `get_market_data`, `get_fund_flow`, `get_stock_news`, and `get_sector_info` all clarified and did not call providers.
* `贵州茅台`: the same four tools clarified and did not call providers.
* `600519`: allowed as `600519.SH`; stock tools ran; data quality summary appeared.
* `600519.SH`: allowed; no false block.

Recommendation:

* Keep both feature flags off by default for now.
* Run one more boundary Web UI retest before default-enable discussion.

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
## Current Recommended Order After Boundary Retest

1. **Default-enable decision for Pre-tool Symbol Guard**
   * Reason: Web UI boundary retest passed for `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.
   * Current view: the guard is a safety layer and is a stronger default-on candidate than the normalizer.
   * User confirmation required: yes.

2. **Keep Symbol Normalizer feature-flagged**
   * Reason: automatic symbol rewriting changes user input semantics.
   * Current view: keep `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` off by default until more market and asset-type boundaries are tested.

3. **Design asset-type-aware tool routing**
   * Reason: `000001.SH` exposed that index prompts can still trigger stock-specific or symbol-less tool calls.
   * Value: separates stock, ETF, index, sector, and market-wide workflows before broader rollout.

4. **Then revisit broader Symbol Normalizer rollout**
   * Reason: normalizer rollout should follow intent guard and asset-type routing stability.

5. **Keep `a-stock-data` adapter deferred**
   * Reason: symbol identity, data freshness, and asset-type routing should be stable before adding new A-share providers.

## Current Recommended Order After Asset-type Routing Design

1. **Implement pure asset-type routing guard + tests**
   * Scope: pure function only, no AgentLoop integration.
   * Candidate module: `agent/src/tools/routing_guard.py`.
   * Business value: prevent index / ETF prompts from reaching unsuitable stock-only tools.

2. **Feature-flagged AgentLoop integration**
   * Scope: run after symbol intent guard and before provider execution.
   * Default: off until retested.
   * Required result shape: structured Tool Routing Blocked / Warning metadata.

3. **Retest Web UI for stock / ETF / index prompts**
   * Test `600519.SH`, `000001.SH`, `510300.SH`, `QQQ.US`, and `00700.HK`.
   * Confirm `Tool Routing Summary` appears when tools are blocked or warned.

4. **Then decide default flags**
   * Pre-tool Symbol Guard: candidate for default-on.
   * Symbol Normalizer: keep feature-flagged until broader asset boundaries are stable.

5. **Keep `a-stock-data` adapter deferred**
   * Reason: a new data source should not be added before tool compatibility policy is explicit.

## Current Recommended Order After Pure Asset-type Guard

1. **Feature-flagged AgentLoop integration**
   * Scope: run `evaluate_tool_asset_compatibility` after Pre-tool Symbol Intent Guard and before provider execution.
   * Default: off.
   * Value: stop wrong tool / asset-type combinations before real provider calls.

2. **Web UI retest asset-type routing**
   * Test `000001.SH`, `510300.SH`, `600519.SH`, `QQQ.US`, and `00700.HK`.
   * Confirm `Tool Routing Summary` or structured routing result appears.

3. **Default-enable decision**
   * Pre-tool Symbol Guard remains a default-on candidate.
   * Symbol Normalizer should remain feature-flagged until asset routing is proven in Web UI.

4. **Keep `a-stock-data` adapter deferred**
   * Reason: new providers should come after routing policy is enforced.

## Current Recommended Order After AgentLoop Asset Routing Integration

1. **Web UI retest asset-type routing**
   * Enable `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1` locally.
   * Test `000001.SH`, `510300.SH`, `600519.SH`, `QQQ.US`, and `00700.HK`.
   * Confirm incompatible stock-only tools are blocked before provider execution.

2. **Decide whether to default-enable Pre-tool Symbol Guard**
   * The symbol guard is safety-oriented and has passed Web UI retests.
   * Asset routing should pass Web UI retest before making default decisions.

3. **Keep Symbol Normalizer feature-flagged**
   * Automatic input rewriting should stay opt-in until more asset-type and market cases pass.

4. **Keep `a-stock-data` adapter deferred**
   * Reason: data-source expansion should follow routing and source-quality enforcement.
