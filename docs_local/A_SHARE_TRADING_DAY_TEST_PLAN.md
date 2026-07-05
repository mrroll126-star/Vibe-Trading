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
* Fund flow/news/financial statement tools either return data or fail with understandable errors.
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
* Error summaries.
* Short report summary.
* Whether the output includes a no-investment-advice boundary.

Do not commit ignored run artifacts. Summarize results in `docs_local/WEB_UI_SMOKE_TEST_REPORT.md` or a future A-share test report.

## 8. Known Risks

* Some providers may lag during trading hours.
* News/web reader may block specific domains.
* A-share symbol normalization is not yet formally designed.
* Detailed run status and run-list status may disagree, as seen in the Phase 0 `600519.SH` test.
* Data freshness should be treated as unverified until compared with an external market data page manually.

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
* Any secret appears in logs or UI.
