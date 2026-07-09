# a-stock-data Financial Statements Integration Plan

Date: 2026-07-09

Status: design only.

This document plans Phase C for the `a-stock-data` work: a feature-flagged fallback path for `get_financial_statements`.

No business code is changed by this document. No live `a-stock-data` endpoint is called. No provider chain is changed.

Implementation update:

Phase C mock-first integration was implemented on 2026-07-09.

Implemented:

* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER`
* Default off behavior.
* Mockable `fetch_a_stock_financials(...)` stub.
* Internal fallback eligibility helper.
* Internal primary-missing/error fallback trigger helper.
* `get_financial_statements` fallback hook after the existing primary path.
* Unit tests and regression tests.

Still not implemented:

* No live `a-stock-data` endpoint call.
* No dependency installation.
* No provider-chain or loader integration.
* No Web UI changes.

## 1. Goal

Add an optional A-share financial-statements fallback path after the existing Vibe-Trading financial-statements source fails or returns no usable rows.

Business goal:

* Improve A-share fundamental coverage for company-level research.
* Keep current Vibe-Trading behavior stable when the feature flag is off.
* Make every fallback result auditable through `_data_quality`, Source Summary, and report warnings.

Recommended first target:

```text
get_financial_statements
```

Why this tool first:

* It is important for investment research.
* It is company-specific, so Asset-type Routing Guard can block indexes and ETFs before the adapter runs.
* It is less intraday-sensitive than fund flow or market data.
* It avoids changing the existing market-data fallback chain.

## 2. Current Baseline

Current tool:

```text
agent/src/tools/financial_statements_tool.py
```

Current sources:

* A-share: Eastmoney F10 financial report datasets.
* Hong Kong: Eastmoney HK F10 financial report datasets.
* US: SEC EDGAR companyfacts.

Current behavior:

* The tool accepts one explicit symbol in `code`, for example `600519.SH`.
* A-share and HK symbols use Eastmoney.
* US symbols use SEC EDGAR.
* It returns a JSON envelope with `ok`, `market`, `source`, `statement`, `period`, and `data`.
* Provider errors are surfaced as `ok=false`.

Already completed Phase B helper:

```text
agent/src/adapters/a_stock_data/normalizer.py
```

The helper is pure. It only normalizes already-provided financial rows into the project contract and does not import, execute, or call `a-stock-data`.

## 3. Non-Goals

This Phase C design does not:

* Replace Eastmoney or SEC EDGAR.
* Change the market-data fallback chain.
* Integrate `a-stock-data` into `get_market_data`.
* Add trading functionality.
* Add iwencai semantic search.
* Add real API keys.
* Vendor-copy the upstream `a-stock-data` Skill into this repository.
* Expose a new public tool to the Agent.
* Disable or weaken Symbol Guard, Asset-type Routing Guard, Source Summary, or Report Gate.

## 4. Feature Flag

Primary flag:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0
```

Default:

```text
off
```

Optional narrower flag if needed:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_FINANCIALS=0
```

Recommendation:

Use the primary flag first. Add the narrower flag only if multiple `a-stock-data` adapters start to exist.

Flag-off behavior:

* `get_financial_statements` behaves exactly as it does now.
* No `a-stock-data` module path is called.
* No new dependency is required at runtime.

Flag-on behavior:

* Only A-share stock financial statements are eligible.
* Existing Eastmoney path remains primary.
* `a-stock-data` is used only as fallback when Eastmoney returns an error, no periods, or unusable rows.
* Fallback output is normalized through `normalize_a_stock_financials_result(...)`.

## 5. Recommended Execution Order

Runtime order should stay conservative:

1. Agent receives a tool call.
2. Symbol Intent Guard checks whether the tool symbol is consistent with the user prompt.
3. Asset-type Routing Guard checks whether `get_financial_statements` is appropriate for the asset type.
4. Existing `get_financial_statements` input validation runs.
5. Existing provider runs first.
6. If existing provider succeeds with usable rows, return existing result.
7. If existing provider fails or returns empty data, check the `a-stock-data` feature flag.
8. If flag is off, return existing failure/empty result.
9. If flag is on and the symbol is an A-share stock, call the `a-stock-data` financial adapter.
10. Normalize adapter output into the project contract.
11. Return result with `_data_quality`.

Important:

`a-stock-data` must never become a shortcut around the guards.

## 6. Eligibility Rules

Eligible:

* `600519.SH`
* `300750.SZ`
* `000001.SZ`
* Other confirmed A-share stocks.

Not eligible:

* A-share indexes such as `000001.SH`.
* ETFs such as `510300.SH` and `159915.SZ`.
* Hong Kong stocks such as `00700.HK`.
* US stocks such as `AAPL.US`.
* Ambiguous raw symbols such as `000001` when not confirmed.
* Chinese names such as `贵州茅台` when not confirmed.

Reason:

The MVP is a company financial-statement fallback. It should not run on instruments that do not have company financial statements or whose identity is ambiguous.

## 7. Fallback Trigger

Use `a-stock-data` only when the existing provider result is not sufficient.

Fallback can trigger when:

* Existing result has `ok=false`.
* Existing result contains a top-level `error`.
* Existing result has no rows for the requested code.
* Existing rows are malformed enough that no period date or financial rows can be used.

Fallback should not trigger when:

* Existing Eastmoney result returns valid periods.
* Market is `us` or `hk`.
* Symbol is not a confirmed A-share stock.
* Asset-type Routing Guard has returned block or ask.
* Feature flag is off.

## 8. Result Shape

The fallback result should keep the same user-facing tool identity:

```text
tool_name = get_financial_statements
```

Recommended envelope:

```json
{
  "ok": true,
  "market": "a_share",
  "source": "a_stock_data",
  "statement": "income",
  "period": "annual",
  "data": {
    "600519.SH": []
  },
  "_data_quality": {
    "600519.SH": {
      "tool_name": "get_financial_statements",
      "provider": "a_stock_data",
      "source": "sina_financial_report",
      "upstream": "a-stock-data",
      "raw_input": "600519.SH",
      "symbol": "600519.SH",
      "normalized_symbol": "600519.SH",
      "freshness_status": "unknown",
      "latest_data_date": "2026-03-31",
      "row_count": 4,
      "source_success": true,
      "source_error": null,
      "warnings": [
        "fallback_used_after_primary_provider_failed"
      ]
    }
  }
}
```

If fallback also fails:

* Return `ok=false`.
* Preserve the primary provider error if useful.
* Add fallback error under `_data_quality`.
* Do not let the report pretend financial statements were available.

## 9. Data Quality Rules

Required:

* `provider`
* `source`
* `tool_name`
* `symbol`
* `normalized_symbol`
* `source_success`
* `source_error`
* `row_count`
* `freshness_status`
* `latest_data_date` when available
* `warnings`

Status rules:

* `missing`: no rows, upstream error, malformed payload, or fallback exception.
* `unknown`: rows exist but no reliable date or requested-date comparison is available.
* `fresh` / `stale`: only later, if the tool has a clear financial-report freshness policy.

Recommendation:

For Phase C, financial statements should usually use `unknown` rather than over-claiming `fresh`. Financial statements are periodic filings, not intraday market data.

## 10. Timeout And Error Handling

Every live fallback call must have:

* Timeout.
* Narrow exception handling.
* No process-wide crash.
* Clear source error string.
* No retry storm.

Recommended timeout:

```text
10 to 15 seconds
```

No fallback call should block the entire Agent run indefinitely.

## 11. Dependency Strategy

Preferred MVP:

* Do not add `a-stock-data` as a package dependency.
* Do not install new global packages.
* Implement a tiny internal HTTP adapter only for the selected financial endpoint after user approval.
* Preserve attribution if any upstream Apache-2.0 logic is adapted.

Alternative:

* Use an optional local vendor clone only for manual exploration, not runtime production.

Do not:

* Import from the readonly vendor clone at runtime.
* Commit vendor code wholesale.
* Write cache files into Git-tracked directories.

## 12. Testing Plan

Pure tests first:

* Existing provider success means no fallback.
* Existing provider `ok=false` plus flag off means original failure is returned.
* Existing provider `ok=false` plus flag on means fallback is attempted for A-share stock.
* Existing provider empty rows plus flag on means fallback is attempted.
* Fallback success returns `_data_quality`.
* Fallback empty returns `missing`.
* Fallback error returns `missing` and `source_error`.
* Index `000001.SH` is blocked before fallback.
* ETF `510300.SH` is blocked before fallback.
* HK and US symbols do not call fallback.
* Ambiguous `000001` and Chinese names do not call fallback without confirmation.

Regression tests:

* Symbol Intent Guard still blocks ambiguous or unconfirmed symbols.
* Asset-type Routing Guard still blocks index/ETF financial statements.
* Source Summary can collect fallback `_data_quality`.
* No Estimate Guard behavior is unchanged.
* Market-wide Benchmark Policy does not bypass financial-statement restrictions.

Live test only after user approval:

* `600519.SH` income annual.
* `300750.SZ` indicators annual.
* Existing provider forced or mocked to fail so fallback behavior can be observed.

## 13. Web UI Acceptance Plan

After tests pass and user approves a local live check:

1. Start backend with:

```bash
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

2. Keep shell tools off.
3. Run a small Web UI prompt:

```text
请分析 600519.SH 最近一期财务表现。请说明使用了哪些财务数据源；如果财务数据缺失，请明确说明，不要估算。
```

Acceptance:

* The report names the source.
* Source Summary includes `get_financial_statements`.
* `_data_quality` includes provider/source/row_count/latest_data_date if available.
* If fallback was used, the report discloses fallback or source warning.
* If data is missing, report does not fabricate revenue, profit, EPS, assets, liabilities, or cash flow.

## 14. Rollback Strategy

Fast rollback:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0
```

Code rollback:

* Revert only the adapter integration commit.
* Keep pure normalizer and design docs if still useful.

Behavioral guarantee:

* Explicit existing symbols such as `600519.SH`, `AAPL.US`, and `00700.HK` must behave the same when the flag is off.

## 15. Open Questions Before Implementation

1. Which exact public endpoint should the first live adapter use: Sina financial report, Eastmoney stock info, or another endpoint documented by `a-stock-data`?
2. Should fallback run only after Eastmoney failure, or should there be an explicit test mode that calls fallback directly?
3. Should financial statements get a stricter periodic freshness policy, such as latest annual or quarterly filing not older than a configured threshold?
4. Should Source Summary show both `provider=a_stock_data` and `source=sina_financial_report`?
5. Should attribution live in code comments, docs, or a local NOTICE section if upstream logic is adapted?

## 16. Recommendation

Proceed with a small Phase C implementation only after user approval:

```text
Feature-flagged fallback in get_financial_statements for confirmed A-share stocks only.
```

Do not touch:

* Market-data fallback chain.
* Web UI.
* Trading tools.
* US/HK financial statements.
* `a-stock-data` fund flow or news.

## 17. Phase C Mock-first Implementation Result

Files added:

* `agent/src/adapters/a_stock_data/financials.py`
* `agent/tests/test_a_stock_data_financials_fallback.py`

Files changed:

* `agent/src/tools/financial_statements_tool.py`
* `agent/src/symbols/config.py`
* `agent/src/adapters/a_stock_data/__init__.py`

Runtime behavior:

* Flag off: old financial-statements behavior is preserved.
* Flag on + primary success: old financial-statements result is returned; fallback is not called.
* Flag on + primary failure/empty + eligible A-share stock: fallback stub is called and normalized through `normalize_a_stock_financials_result(...)`.
* Flag on + index/ETF/US/HK/ambiguous/Chinese name: fallback is not called.
* Default fetch stub returns `a_stock_data_live_fetch_not_implemented` and normalizes to `missing`.

Feature flag:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0
```

Default remains off.

Next step:

Design a controlled live smoke test before any real endpoint is added or called.

Controlled live smoke design:

Added on 2026-07-09:

* `docs_local/A_STOCK_DATA_LIVE_SMOKE_TEST_PLAN.md`

Recommendation:

* Use an external one-off smoke script first.
* Do not enter AgentLoop.
* Do not modify `get_financial_statements`.
* Do not call live endpoints until user explicitly approves.
* Keep `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0` by default.

Candidate endpoint:

* `sina_financial_report(code, report_type, num)` from the upstream Skill.
* First live smoke should inspect raw output shape only.
