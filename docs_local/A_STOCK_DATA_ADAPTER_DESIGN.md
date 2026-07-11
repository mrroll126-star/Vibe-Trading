# a-stock-data Adapter Design

## 1. Background

Phase 1 guardrail baseline is now in place:

* Data freshness metadata.
* Source Summary / Missing Data / Source Warnings.
* Time-sensitive Report Gate.
* No Estimate Warning MVP.
* Pre-tool Symbol Intent Guard, default on.
* Asset-type Routing Guard, default on.
* Symbol Normalizer, default off.
* Market-wide Benchmark Policy, feature-flagged and default off.
* Benchmark batch handling fixed and retested through the API/Web UI same-origin path.

Core principle:

Do not add more data before the system can prove where the data came from, whether it is fresh, and whether the tool call was appropriate.

中文：

在系统能证明数据来源、新鲜度和工具适配性之前，不应盲目增加数据源。

This document is design only. It does not integrate `a-stock-data`, modify provider chains, modify loaders, or change Web UI behavior.

Phase D update:

The financial-statement adapter path is no longer design-only. A live Sina financial fetch now exists behind `fetch_a_stock_financials(...)`, but it remains constrained by the existing feature flag and fallback-only hook:

* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.
* Existing primary financial providers still run first.
* The adapter supports only financial statements for confirmed A-share stocks.
* Supported statements are `income`, `balance`, and `cashflow`.
* `indicators`, fund flow, news, reports, provider-chain integration, loader integration, and Web UI integration remain out of scope.
* This document remains the design reference for broader future adapter work.

Phase F output-structure observation update:

The official `get_financial_statements` fallback output was inspected directly on 2026-07-10. The observed fallback result contains the fields needed by report-layer Source Summary:

* top-level `provider=a_stock_data`
* top-level `source=sina_financial_report`
* top-level `upstream=a-stock-data`
* rows under `data[SYMBOL]`
* `_data_quality[SYMBOL]`
* `latest_data_date`
* `warnings`
* `primary_error`

This means the current financial fallback shape is suitable for report-layer consumption without changing provider chains, loaders, or Web UI.

Phase G report-summary observation:

The fallback output was passed through the existing report-summary helpers. The summary layer successfully displayed:

* `get_financial_statements`
* `sina_financial_report`
* `row_count=8`
* `latest_data_date=2026-03-31`
* fallback warnings

No Estimate Guard did not produce a false warning, and Report Gate did not block the financial report observation. The only product nuance is that `freshness_status=unknown` causes a `Missing Data` section, which is acceptable for MVP auditability but should be revisited with a financial filing freshness policy.

## 2. Current A-share Data Baseline

Current market-data fallback chain:

```text
tencent -> mootdx -> eastmoney -> baostock -> akshare -> tushare -> local
```

Current stable or usable areas:

* `get_market_data`: A-share daily market data is integrated through the loader registry and now gets `_data_quality`.
* `get_stock_news`: A-share stock and global news use Eastmoney and now get `_data_quality`.
* `get_fund_flow`: Eastmoney fund-flow data gets `_data_quality`.
* `get_research_reports`: Eastmoney + THS-style research reports get `_data_quality`.
* `get_sector_info(mode=ranking)`: useful as a market-wide sector ranking tool, and no-symbol calls are exempted from symbol guard.
* Market-wide benchmark calls are controlled by the benchmark policy when enabled.

Current unstable or incomplete areas:

* `fund_flow` can hit Eastmoney connection reset / aborted responses.
* `research_reports` can return A-share-only errors or upstream 400-style failures.
* `northbound_flow` can return empty or unreliable data, and the candidate source itself notes that Eastmoney northbound fields have had upstream issues since 2024.
* `financial_statements`, `margin_trading`, `shareholder_count`, `block_trades`, `sector_info`, `northbound_flow`, `dragon_tiger`, and market screener return structured envelopes, but do not yet all share the same `_data_quality` contract.
* `TUSHARE_TOKEN` is not configured.
* Some AkShare paths may fail or return empty results.
* yfinance TLS remains a known issue, mostly affecting US/HK/profile-style paths rather than A-share core data.

Tools already connected to `_data_quality`:

* `get_market_data`
* `get_fund_flow`
* `get_stock_news`
* `get_research_reports`

Tools that need fuller `_data_quality` before adding more source logic:

* `get_financial_statements`
* `get_margin_trading`
* `get_shareholder_count`
* `get_block_trades`
* `get_sector_info`
* `get_northbound_flow`
* `get_dragon_tiger`
* `screen_market`

How current provider data reaches Source Summary:

* Tools return `_data_quality`.
* Report code collects tool-returned quality metadata.
* `docs_local` guardrail work established `Data Source Summary`, `Missing Data`, and `Source Warnings`.
* If a new adapter does not return `_data_quality`, it will be less auditable than the current guarded paths.

## 3. a-stock-data Capability Summary

Readonly source investigated:

* Repository: `https://github.com/simonlin1212/a-stock-data`
* Local readonly clone: `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/_vendor_readonly/a-stock-data`
* Observed commit: `bcda405 feat: 新增打板/ETF期权/舆情互动三层 (v3.3.0 · #13 #23 #15)`

Project shape:

* Not a conventional Python package in the current repo shape.
* Not an MCP server.
* Not an HTTP service.
* It is primarily a Skill-style Markdown artifact with embedded Python snippets and helper functions.
* The README says Codex/OpenClaw users can paste the `SKILL.md` content into context; this is useful for human-assisted exploration but is not suitable as a direct production dependency.

License:

* Apache License 2.0.
* This is generally integration-friendly, but any copied or adapted code must preserve required attribution and license notices.

Declared dependencies:

* `mootdx`
* `requests`
* `pandas`
* `stockstats`

Declared dependency strategy:

* V3.0 removed AkShare dependency.
* Most data sources are direct HTTP APIs or mootdx TCP.
* Eastmoney requests use a shared `em_get()` helper with serial throttling, jitter, session reuse, and retry.

Authentication:

* Most data sources are described as free and no-key.
* `iwencai` semantic search requires an `IWENCAI_API_KEY` / X-Claw-style API key.
* Some endpoints may still face IP-level throttling or anti-bot behavior.

Data types advertised:

| Area | Claimed capability |
| --- | --- |
| Market data | K-line, realtime quote, order book, tick trades, index, ETF |
| Fundamentals | Quarterly snapshot, F10 profile, Eastmoney stock info, Sina financial statements |
| Financial forecasts / valuation | THS EPS consensus, PE/PEG-style workflows |
| Fund flow | Eastmoney minute flow and 120-day daily fund flow |
| News | Eastmoney stock news and global finance news |
| Announcements | CNINFO announcements and mootdx F10 announcement summaries |
| Research reports | Eastmoney stock reports, industry reports, PDF download, iwencai semantic report search |
| Sector / concept | Eastmoney concept blocks, industry/concept/region membership |
| Northbound | THS realtime minute flow and self-cached historical daily flow |
| Margin trading | Eastmoney datacenter margin data |
| Block trades | Eastmoney datacenter block trades |
| Shareholder count | Eastmoney datacenter shareholder changes |
| Dragon tiger | Eastmoney datacenter and seat-level data |
| Lock-up / dividend | Eastmoney datacenter lock-up and dividend history |
| Limit-up / sentiment | Eastmoney limit-up/down pools, THS limit-up reasons, sentiment metrics |
| ETF options | Sina option codes, T-quotes, Greeks, implied volatility |
| Investor interaction / popularity | CNINFO IRM, THS hot list, Eastmoney hot rank and concepts |

Fields and dates:

* Many snippets describe date fields such as `date`, `publishDate`, `reportDate`, `datetime`, and provider-specific fields.
* Field shapes are endpoint-specific.
* There is no single normalized return contract in the candidate project.
* There is no guaranteed project-wide `_data_quality` equivalent.

Asset type support:

* README explicitly says A-share indexes and ETFs are supported by Tencent/mootdx-style quote paths.
* ETF options are a separate layer.
* Stock / index / ETF separation is described, but not in a unified typed contract.

Batch support:

* Some examples imply batch comparison workflows.
* Endpoint-level batch support varies and must be verified per adapter.

Cache:

* Northbound history uses a local CSV self-cache under a home-directory cache path in the Skill example.
* A direct integration must not write such cache files into Git and should either avoid cache in MVP or route it through this project's ignored local cache conventions.

Limitations:

* It is broad and powerful, but not a drop-in dependency.
* It contains many direct public web endpoints that may change.
* Eastmoney rate-limit and IP-throttling risk remains.
* Some code snippets are intended for AI assistant use, not stable library APIs.
* Upstream README includes historical fixes, which is useful context but also indicates endpoint churn.

## 4. Integration Options

### Option A: Loader-level provider

Add a new A-share market-data provider to the existing loader fallback chain, for example:

```text
tencent -> a_stock_data -> eastmoney -> akshare -> local
```

Advantages:

* Fits the current market-data architecture.
* Easier to reuse existing freshness and source summary machinery.
* Suitable for OHLCV / quote-style data if fields are normalized.

Disadvantages:

* Only fits market data well.
* Higher risk of changing existing fallback behavior.
* Field mapping must be strict.
* Could make a new broad dependency affect a path that already works reasonably well.

### Option B: Tool-level adapter

Add `a-stock-data` fallback inside one existing tool at a time, for example financial statements, fund flow, sector info, or research reports.

Advantages:

* Targets real gaps.
* Lower blast radius.
* Each tool can have its own contract tests.
* Does not disturb the market-data chain.
* Easier to require `_data_quality` and source warnings per tool.

Disadvantages:

* More integration points over time.
* More repeated field mapping unless a shared adapter contract is designed.
* Needs careful feature flags.

### Option C: Separate experimental tool namespace

Add tools such as `experimental_a_stock_data_fund_flow` or `experimental_a_stock_data_financials`.

Advantages:

* Lowest risk to existing behavior.
* Easy to audit and compare against existing sources.
* Good for exploration.

Disadvantages:

* The Agent may choose experimental tools too freely unless routing is strict.
* Later migration into official tools is extra work.
* Users may see duplicate or confusing tool options.

Recommendation:

Start with Option B, tool-level fallback, but build a small shared adapter-normalization layer first. Do not replace the market-data fallback chain in the MVP.

## 5. Recommended MVP

Recommended MVP:

```text
A-share financial statements fallback, behind a feature flag, with pure normalization helpers and tests first.
```

Why this MVP:

* Current `get_financial_statements` is important for investment research.
* It is company-specific, so Asset-type Routing Guard can clearly block indexes and ETFs before the adapter.
* It is less time-sensitive than intraday fund flow, so freshness risks are easier to handle conservatively.
* It avoids disturbing the market-data chain.
* `a-stock-data` advertises Sina financial statements and fundamental data, which directly overlaps this gap.
* A statement adapter can require strong field normalization and explicit date handling before any report consumes it.

Why not fund flow first:

* Fund flow is time-sensitive and source-fragile.
* Eastmoney connection reset has already been observed.
* If added too early, it may increase "today" hallucination pressure unless the report gate is extended further.

Why not market data first:

* Current A-share market-data fallback already exists and is guarded.
* Replacing or inserting a new provider into the loader chain would risk changing known working behavior.
* Market-wide benchmark and freshness behavior should stay stable while the new source is evaluated.

MVP feature flag:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1
```

Default:

```text
off
```

Potential later sub-flags:

* `VIBE_TRADING_ENABLE_A_STOCK_DATA_FINANCIALS`
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_FUND_FLOW`

Do not add many flags in the first MVP unless needed.

## 6. Data Quality Contract

Every `a-stock-data` adapter result must normalize to this shape before a report can use it:

```json
{
  "ok": true,
  "symbol": "600519.SH",
  "provider": "a_stock_data",
  "source": "sina_financial_report",
  "as_of_date": "2026-03-31",
  "rows": [],
  "_data_quality": {
    "600519.SH": {
      "tool_name": "get_financial_statements",
      "raw_input": "600519.SH",
      "normalized_symbol": "600519.SH",
      "symbol": "600519.SH",
      "source": "sina_financial_report",
      "provider": "a_stock_data",
      "latest_data_date": "2026-03-31",
      "freshness_status": "fresh",
      "source_success": true,
      "source_error": null,
      "row_count": 1,
      "warnings": []
    }
  }
}
```

Required rules:

* Must include `provider`.
* Must include `source`.
* Must include `as_of_date` when the upstream source exposes one.
* If no date can be extracted, mark `_data_quality.freshness_status=unknown`.
* If no rows are returned, mark `missing`.
* If upstream errors, mark `missing` with `source_error`.
* Strong time-sensitive prompts must still be controlled by report gates.
* The adapter must not return analysis text. It returns data and metadata only.

## 7. Guardrail Interaction

`a-stock-data` must not be directly callable as a shortcut around the existing guardrails.

Required order:

1. Symbol Intent Guard.
2. Market-wide Benchmark Policy if enabled.
3. Asset-type Routing Guard.
4. Existing tool entry point.
5. Feature-flag check.
6. `a-stock-data` adapter/provider.
7. Data Quality / Freshness metadata.
8. Source Summary / Report Gate.

This means:

* A Chinese company name still requires confirmation in MVP.
* Ambiguous codes such as `000001` still require clarification.
* Indexes and ETFs must not reach company-specific financial-statement adapters.
* `a-stock-data` output must enter the same Source Summary as current providers.

## 8. Feature Flag Plan

Primary flag:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0
```

Default:

```text
0 / off
```

Flag-off behavior:

* Existing tools behave exactly as they do now.
* No `a-stock-data` code path is called.
* No new dependency is required.

Flag-on MVP behavior:

* Only the selected MVP tool can call the adapter.
* Adapter failures fall back to the existing behavior or return a clearly disclosed missing-data result, depending on the chosen integration point.
* No provider chain is globally changed.

## 9. Testing Plan

Minimum tests:

1. Flag off produces zero behavior change.
2. Flag on + supported A-share stock calls the adapter.
3. Flag on + unsupported asset type, such as index, is blocked by Asset-type Routing before adapter.
4. Adapter success returns `_data_quality`.
5. Adapter empty result returns `missing`.
6. Adapter error returns `missing` plus source warning.
7. Adapter result without date returns `unknown`.
8. Source Summary includes `a_stock_data`.
9. Stale data plus time-sensitive prompt is blocked by the report gate when the tool participates in time-sensitive reports.
10. No sensitive files, cache files, or vendor code are committed.

Recommended test style:

* Start with pure normalization helpers and fixtures.
* Do not call real public endpoints in unit tests.
* Use mock adapter responses for success, empty, error, no-date, and stale-date cases.

## 10. Rollout Plan

Phase A: design only.

* This document.
* No code integration.

Phase B: pure adapter normalization helpers + tests.

* Parse a small subset of candidate source fields into the project contract.
* No provider calls.
* No tool integration.

Status:

Completed on 2026-07-09.

Added files:

* `agent/src/adapters/a_stock_data/normalizer.py`
* `agent/src/adapters/a_stock_data/__init__.py`
* `agent/src/adapters/__init__.py`
* `agent/tests/test_a_stock_data_normalizer.py`

Normalized contract:

* `provider`: always `a_stock_data`.
* `source`: upstream adapter source name, defaulting to `a_stock_data`.
* `upstream`: descriptive upstream source name, defaulting to `unknown`.
* `statement_type`: optional passthrough for income / balance sheet / cash flow style routing.
* `data`: keyed by symbol, with normalized rows.
* `_data_quality`: keyed by symbol, using the same fields expected by Source Summary.

Current status rules:

* Empty, `None`, malformed, or explicit upstream error payloads return `ok=false` and `freshness_status=missing`.
* Rows with a date return `ok=true`, preserve `latest_data_date`, and use `freshness_status=unknown` because there is no requested date in this pure helper.
* Rows without a date return `ok=true`, `freshness_status=unknown`, and warning `no_as_of_date`.

Supported first-pass date fields:

* `report_date`
* `reportDate`
* `date`
* `end_date`
* `endDate`
* `period`
* `报告期`
* `公告日期`
* `截止日期`

Supported first-pass financial field aliases:

* `revenue` / `operating_revenue` / `营业收入`
* `net_profit` / `netProfit` / `净利润` / `归母净利润`
* `total_assets` / `totalAssets` / `总资产`
* `total_liabilities` / `totalLiabilities` / `总负债`
* `cash_flow` / `operating_cash_flow` / `经营现金流` / `经营活动现金流`
* `eps` / `basic_eps` / `每股收益` / `基本每股收益`

Boundary:

This helper does not import, execute, clone, or vendor `a-stock-data`. It does not read local files, call the network, install dependencies, or change any tool/provider behavior.

Phase C: feature-flagged single-tool integration.

* Recommended first target: `get_financial_statements`.
* Keep existing source as primary unless user approves fallback order.
* Add adapter only as a controlled fallback or explicit internal provider path.

Status:

Design document added on 2026-07-09:

* `docs_local/A_STOCK_DATA_FINANCIALS_INTEGRATION_PLAN.md`

Recommended Phase C shape:

* Feature flag: `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0` by default.
* Existing Eastmoney A-share financial statements remain primary.
* `a-stock-data` can be used only as fallback after existing provider failure or empty unusable rows.
* Eligible symbols: confirmed A-share stocks only.
* Ineligible: indexes, ETFs, HK, US, ambiguous raw symbols, and Chinese names without confirmation.
* Fallback output must include `_data_quality`.
* No live endpoint call should be added without user approval.

Phase C mock-first implementation status:

Completed on 2026-07-09.

Implemented:

* Feature flag `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER`, default off.
* `agent/src/adapters/a_stock_data/financials.py`.
* Mockable `fetch_a_stock_financials(...)` default stub.
* Fallback eligibility and primary-result trigger helpers.
* `get_financial_statements` hook after the existing primary path.
* Unit tests proving flag-off zero behavior, primary-success no fallback, eligible A-share fallback, ineligible symbol refusal, and default not-implemented behavior.

Still deferred:

* Live `a-stock-data` endpoint selection.
* Live smoke testing.
* Any provider-chain or loader integration.
* Any fund-flow/news/research-report adapter.

Live smoke design status:

Added on 2026-07-09:

* `docs_local/A_STOCK_DATA_LIVE_SMOKE_TEST_PLAN.md`

Recommended first live candidate:

* `sina_financial_report` from the upstream Skill.
* Statement mapping:
  * `income` -> `lrb`
  * `balance` -> `fzb`
  * `cashflow` -> `llb`
* `indicators` remains unknown for this candidate.

Recommended execution mode:

* Option A: external one-off smoke script outside AgentLoop and outside `get_financial_statements`.

One-off smoke result:

Completed on 2026-07-09.

* Script: `scripts/smoke_a_stock_data_financials.py`
* `600519.SH income`: success, 3 rows, `报告期` detected, normalized ok.
* `300750.SZ income`: success, 3 rows, `报告期` detected, normalized ok.
* Local output: `local_reports/a_stock_data_smoke_20260709_152952.json`

The output file is ignored and not committed.

Phase D: CLI/direct tests.

* Mock first.
* Then optional live smoke only after user approval.

Phase E: Web UI tests.

* Verify Source Summary.
* Verify missing/stale/unknown warnings.
* Verify no silent bypass of Symbol Guard or Asset-type Routing.

Phase F: decide expansion.

* Consider fund flow, sector info, research reports, announcements/news, or shareholder count based on observed gaps.

## 11. Risks

* Upstream public APIs can change without notice.
* Eastmoney and other public sites may rate-limit or block IPs.
* Field names differ across endpoints.
* Some endpoints may not expose reliable dates.
* Data口径 may conflict with existing providers.
* Adding another source can make the Agent over-trust new data unless Source Summary is strict.
* Latency and token cost may increase.
* License attribution must be handled correctly if code is adapted.
* Vendor code must not be copied wholesale into this repo.
* Local cache paths in the candidate project must not write into Git.
* iwencai requires an API key and should be excluded from the MVP unless explicitly approved.
* The candidate project is a Skill document, not a stable package API.

## 12. Open Questions

* Should MVP use existing Eastmoney financial statements as primary and `a-stock-data` only as fallback, or vice versa?
* Which exact financial statement endpoint should be normalized first: Sina three statements, Eastmoney stock info, or mootdx financial snapshot?
* Should live smoke tests be allowed against public endpoints after pure tests pass?
* Where should attribution be placed if code snippets are adapted under Apache-2.0?
* Should cache be disabled entirely in MVP?
* Do we want `a-stock-data` as an internal adapter only, or later expose source names in user-facing reports?
* Should Source Summary show both `provider=a_stock_data` and the upstream source such as `sina` or `eastmoney`?
* Should `iwencai` be treated as a separate future provider because it requires a key?
