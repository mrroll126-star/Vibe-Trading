# A-Share Trading Day Test Plan

Status: planned.

Target date: 2026-07-06, Monday.

Purpose: verify how the existing Vibe-Trading A-share workflow behaves on a real A-share trading day, without adding `a-stock-data` and without changing provider logic.

This plan is for product validation and data workflow testing only. It is not investment advice.

## 1. Why This Test Comes Next

The 2026-07-05 Web UI smoke test showed that `600519.SH` can trigger A-share oriented tools and produce a report.

However, 2026-07-05 is Sunday, so the result was based on the latest available prior trading data and web/news context. A trading-day test is needed to check whether current-day A-share data, news, fund flow, and report tools behave consistently during market hours or after market close.

## 2. Safety Boundaries

Do not:

* Integrate `a-stock-data`.
* Replace original Vibe-Trading providers.
* Modify fallback chains.
* Enable shell tools.
* Connect broker/trading execution.
* Ask the Agent for buy/sell decisions.
* Expose Web UI outside localhost unless separately approved.

Keep:

* `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* `API_AUTH_KEY` configured in ignored `agent/.env`.
* Services bound to `127.0.0.1` for local testing.

## 3. Recommended Symbols

Primary:

* `600519.SH` - 贵州茅台, high-liquidity large-cap A-share.

Secondary:

* `300750.SZ` - 宁德时代, liquid growth/industrial chain symbol.
* `000001.SZ` - 平安银行, simple Shenzhen main-board example.

Do not use bare symbols such as `600519` in this test. The Phase 0 symbol finding suggests explicit suffixes are safer.

## 4. Recommended Test Windows

If the user is available:

* Morning after open: check whether intraday/current-day fields appear.
* Midday break: check whether data remains stable.
* After close: check whether latest close, fund flow, and news update more consistently.

If there is only one window, prefer after market close because it is easier to evaluate daily data consistency.

## 5. Web UI Test Prompts

Primary prompt:

```text
请生成 600519.SH 的简短研究摘要，包括今日走势、最近交易日变化、主要风险和后续关注点。不要给买卖建议。
```

Secondary prompt:

```text
请生成 300750.SZ 的简短研究摘要，包括今日走势、最近交易日变化、主要风险和后续关注点。不要给买卖建议。
```

Optional compare prompt:

```text
请比较 600519.SH 和 300750.SZ 最近交易日表现、资金面和主要风险。只做研究分析，不给买卖建议。
```

## 6. Validation Checklist

Pass criteria:

* Web UI can submit the prompt.
* Agent run completes or fails with a clear reason.
* Report is visible in Web UI.
* Trace shows at least one A-share data-oriented tool call.
* Report includes data date or timing context.
* Report avoids buy/sell advice.
* No shell tools are enabled.
* No secret keys are printed.

Data quality checks:

* Symbol is recognized as A-share.
* Latest price/date is plausible.
* If current-day data is unavailable, the report says so clearly.
* If data timestamp is missing or unknown, the report says freshness is unknown.
* The report does not invent today's close, percent change, volume, turnover, fund flow, news, announcements, or financial facts.
* Fund flow/news/financial statement tools either return data or fail with understandable errors.
* Provider failures are visible in the report or source summary, not only in trace.
* The run-list status matches the detailed run status.

## 7. Evidence To Record

For each test, record:

* Prompt.
* Web session ID.
* Run ID.
* Start/end time.
* Status shown in Web UI.
* Status shown in `/runs`.
* Status shown in `/runs/<run_id>`.
* Tool calls from local trace.
* Whether current-day data was obtained.
* Data date or timestamp shown by each tool.
* Provider/source success, skipped, failed, empty, or timestamp-unknown status.
* Error summaries.
* Short report summary.
* Whether missing data was disclosed clearly.
* Whether the report made factual claims without returned data.
* Whether the output includes a no-investment-advice boundary.

Do not commit ignored run artifacts. Summarize results in `docs_local/WEB_UI_SMOKE_TEST_REPORT.md` or a future A-share test report.

## 8. Known Risks

* Some providers may lag during trading hours.
* News/web reader may block specific domains.
* A-share symbol normalization is not yet formally designed.
* Detailed run status and run-list status may disagree, as seen in the Phase 0 `600519.SH` test.
* Data freshness should be treated as unverified until compared with an external market data page manually.
* The Agent may still produce factual-sounding conclusions if a tool fails; this is the reason Data Freshness & Anti-Hallucination Guardrails are now a Phase 1 priority before `a-stock-data`.

## 9. Go / No-Go Rule

Proceed only when:

* DeepSeek key remains configured locally.
* API auth remains configured.
* Shell tools remain disabled.
* User explicitly confirms the trading-day validation run.

Stop and document if:

* The Agent asks for shell tools.
* The task attempts trading/broker actions.
* The report gives direct buy/sell recommendations.
* The report invents current-day price, change, volume, turnover, fund-flow, news, or financial facts that are not present in tool outputs.
* Any secret appears in logs or UI.

## 10. Preflight Result Before Trading Day

Date: 2026-07-05.

Level 1 lightweight market-data test:

* Symbols: `600519.SH`, `300750.SZ`, `000001.SZ`, `601318.SH`, `510300.SH`, `159915.SZ`.
* Providers checked: `tencent`, `mootdx`, `eastmoney`, `baostock`, `akshare`, `tushare`, `local`.
* Local JSON report: `local_reports/a_share_preflight_20260705.json`.
* The local report is ignored by Git and was not committed.

Result summary:

| Symbol | Basic OHLCV Result | Working Provider(s) | Notes |
| -- | -- | -- | -- |
| `600519.SH` | success | `tencent` | 31 rows returned. |
| `300750.SZ` | success | `tencent` | 31 rows returned. |
| `000001.SZ` | success | `tencent` | 31 rows returned. |
| `601318.SH` | success | `tencent` | 31 rows returned. |
| `510300.SH` | success | `tencent`, `akshare` | 31 rows returned from both. |
| `159915.SZ` | success | `tencent`, `akshare` | 31 rows returned from both. |

Provider observations:

* `tencent`: succeeded for all six symbols and is the most reliable basic A-share OHLCV source in this preflight.
* `akshare`: succeeded for the two ETF symbols, failed or returned no rows for the four stock symbols in this run.
* `eastmoney`: failed or returned no rows in the lightweight loader test; previous Agent tasks still used some Eastmoney-backed A-share tools successfully.
* `mootdx`: dependency missing in this local environment.
* `baostock`: dependency missing in this local environment.
* `tushare`: token is not configured.
* `local`: no local data bridge config for these symbols.

Level 2 minimal research tasks:

| Symbol | Run ID | Result | Elapsed | Tool Summary | Main Errors |
| -- | -- | -- | -- | -- | -- |
| `600519.SH` | `20260705_170327_44_d10190` | success | about 2m20s | market data, financial statements, news, research reports, fund flow, margin trading, shareholder count, sector info, northbound flow, block trades, web search, URL reading | yfinance preflight still failed; Tushare token not set; Yahoo profile SSL appeared but did not fail the run. |
| `300750.SZ` | `20260705_170559_16_fc55fe` | success | about 2m57s | market data, news, research reports, financial statements, sector info, margin trading, shareholder count, web search, URL reading | yfinance preflight still failed; Tushare token not set. |

Interpretation:

* The original Vibe-Trading A-share workflow is usable enough for a real trading-day trial.
* Current basic OHLCV fallback appears heavily dependent on `tencent` in this environment.
* A-share secondary tools can enrich reports, but provider reliability is uneven.
* Tomorrow's test should focus on usefulness, data freshness, and missing information before planning `a-stock-data`.

## 11. Real Trading-Day Recording Template

Use this table on 2026-07-06:

| 时间 | 标的 | 场景 | Prompt | 是否成功 | Run ID | 调用工具 | 数据源 | 是否拿到当天数据 | 数据 timestamp/date | provider 成功/失败 | 错误摘要 | 是否披露缺失数据 | 是否无数据却下结论 | 输出是否有用 | 需要改造 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 开盘前 | `600519.SH` | 基础概览 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 开盘前 | `300750.SZ` | 基础概览 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 盘中 |  | 盘中观察 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 收盘后 |  | 总结复盘 |  |  |  |  |  |  |  |  |  |  |  |  |  |

## 12. Suggested Test Rhythm For 2026-07-06

### Before Market Open

* Test `600519.SH` basic overview.
* Test `300750.SZ` basic overview.
* Confirm whether the report clearly says data is from the latest prior trading day.

### During Market Hours

* Observe only; do not ask for trading advice.
* Focus on whether data is real-time, near-real-time, delayed, or stale.
* Record whether fund flow, news, and sector information update.

### After Market Close

* Run one summary-style task.
* Evaluate whether the report is useful as a daily review note.
* Compare the report date/price/fund-flow claims against an external market-data page manually.

### Key Judgments For Tomorrow

* Is the original A-share data good enough for daily research?
* Does the Agent clearly state whether it has today's data?
* Does the Agent expose provider success/failure and data timestamps?
* Does the Agent clearly disclose missing or stale data?
* Does the Agent ever make factual market claims without tool-returned data?
* When does `a-stock-data` become necessary?
* Which information is most missing: fund flow, announcements, news, research reports, sector data, or sentiment?
* Is the Agent output too generic?
* Is a fixed research report template needed?
* Which freshness guardrails are needed before any A-share data-source expansion?
