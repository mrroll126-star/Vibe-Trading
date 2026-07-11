# MVP Research Workspace Design

## 1. Product Positioning

The first product surface should not be a generic AI stock chat page.

Recommended positioning:

```text
AI Investment Research Workspace
```

The workspace helps an investor move through a repeatable research loop:

```text
discover opportunity
    -> understand the company
    -> validate the thesis
    -> identify risks
    -> form a documented investment view
```

The first version should turn the existing trusted data and Agent foundation
into one focused stock research workflow.

## 2. User Entry

The first version should keep the entry simple:

```text
请输入股票代码 / 公司名称

Examples:
600519
贵州茅台
AAPL
00700
```

Expected routing:

```text
User input
    -> Symbol Normalizer
    -> Symbol Intent Guard
    -> Asset-type Routing Guard
    -> Research Workflow
    -> Report Schema
    -> UI
```

Important behavior:

* Explicit symbols such as `600519.SH`, `AAPL.US`, and `00700.HK` should pass.
* Ambiguous symbols such as `000001` should request clarification.
* Chinese names such as `贵州茅台` should not be silently converted unless a
  confirmation mechanism exists.
* Market-wide questions should use Benchmark Policy only when enabled and
  auditable.

## 3. Page Structure

The MVP page should have five sections.

## Section 1: Market Snapshot

Purpose:

Answer:

```text
当前市场状态如何？
```

For a single stock, show:

```text
symbol
company name
current price
price change
trend
volume / turnover
relative strength
market benchmark
```

Data source:

* Existing market data tools.
* Existing `_data_quality` metadata.

For market-wide research, show:

```text
Market Benchmark

000300.SH
399006.SZ
SPY.US
QQQ.US
```

Benchmark requirements:

* Benchmarks must come from an auditable benchmark universe.
* Non-benchmark individual stocks should not be silently selected as market
  proxies.
* Benchmark Policy should remain feature-flagged until product behavior is
  accepted.

## Section 2: Financial Health

Purpose:

Show the company's core financial condition from raw financial statements.

Current available inputs:

```text
income
balance
cashflow
```

Suggested content:

```text
Revenue
Net Profit
Total Assets
Total Liabilities
Operating Cash Flow
Latest Reporting Period
```

The first version should not be only a raw table. It should include a short AI
summary:

```text
过去几个报告期：

收入趋势：
利润趋势：
现金流趋势：
资产负债变化：
```

Source disclosure:

```text
provider: a_stock_data
source: Sina Financial Report
period: 2026-03-31
warnings:
- primary_financials_unavailable
- a_stock_data_fallback_used
```

Important boundary:

* Financial statements are not real-time data.
* Financial data should use reporting-period language, not intraday freshness
  language.

## Section 3: AI Analyst Memo

Purpose:

Convert structured data into a reusable research memo.

The Agent should not free-write an unbounded essay. The memo should follow a
stable structure:

```text
Investment Thesis

Bull Case
1.
2.

Bear Case
1.
2.

Key Risks
1.
2.

What To Monitor
1.
2.
```

Policy:

* Separate facts from interpretation.
* Do not give buy/sell instructions.
* Do not invent forecasts, target prices, or analyst estimates.
* Mention missing data where relevant.
* Use source dates and provider names from Data Confidence.

## Section 4: Valuation & Metrics

Purpose:

Reserve space for future Metrics Engine and Valuation Engine without
overpromising today.

Current status:

```text
Partial
```

Reason:

Valuation requires:

```text
Financial Data
+ Market Data
+ Market Cap / Shares Outstanding
+ Period Alignment
```

First version display:

```text
Valuation & Metrics

Status:
Partial

Available:
- Historical revenue and profit data
- Balance sheet data
- Cash-flow data

Not yet available:
- PE
- PB
- ROE
- ROIC
- Analyst forecast
- Target price

Reason:
Requires Metrics Engine and market-cap/share data.
```

## Section 5: Data Confidence

Purpose:

This is the product's differentiator. The user should see not only the answer,
but also what data the system actually had.

Suggested display:

```text
Data Confidence

Market Data
Provider:
Tencent / Yahoo / other actual provider

Date:
2026-07-11

Status:
OK / stale / missing / unknown

Financial Data
Provider:
a_stock_data

Source:
Sina Financial Report

Period:
2026-03-31

Status:
Available

Warnings:
- Primary financial provider unavailable
- Fallback used
```

The Data Confidence section should be visible, not hidden in logs.

## 4. Report Schema

The UI should not consume only free-form natural language. It should consume a
stable report schema.

Initial schema:

```json
{
  "symbol": "",
  "display_name": "",
  "asset_type": "",
  "market_snapshot": {
    "status": "",
    "price": null,
    "change_pct": null,
    "volume": null,
    "turnover": null,
    "trend_summary": "",
    "benchmark": {}
  },
  "financial_health": {
    "status": "",
    "latest_period": "",
    "income": {},
    "balance": {},
    "cashflow": {},
    "summary": "",
    "warnings": []
  },
  "investment_memo": {
    "investment_thesis": "",
    "bull_case": [],
    "bear_case": [],
    "key_risks": [],
    "what_to_monitor": []
  },
  "valuation": {
    "status": "partial",
    "available_metrics": [],
    "missing_inputs": [],
    "notes": ""
  },
  "data_confidence": {
    "market_data": {},
    "financial_data": {},
    "warnings": []
  }
}
```

Design principle:

```text
Web UI
    -> Report Schema
    -> Agent Workflow
    -> Tools
    -> Data Quality
```

The schema should become the contract between Agent output and the Research
Workspace UI.

## 5. MVP Explicitly Does Not Do

The first Research Workspace must not drift into a trading product.

Not included:

* Automatic buy/sell decisions.
* Investment recommendation score.
* Target price prediction.
* AI stock picking.
* Real-time watch/alert system.
* Complex portfolio management.
* Trade execution.
* Unsupported analyst forecasts.
* Unverified peer comparison.

Reason:

The first product goal is trusted research workflow, not automated trading or
prediction.

## 6. First-version Acceptance Criteria

Input:

```text
600519
```

Expected output:

* The system either normalizes/clarifies the symbol safely or asks for
  confirmation.
* Company/stock context is shown.
* Market Snapshot appears if market data is available.
* Financial Health appears with income, balance, and cash-flow information.
* AI Analyst Memo appears in the fixed structure.
* Data Confidence appears with provider, source, date/period, and warnings.
* Fallback status is visible if primary financial provider failed.
* Missing or unsupported metrics are disclosed.
* No buy/sell recommendation is produced.
* No target price is invented.
* No forecasts are invented.

## 7. Recommended Implementation Sequence

Do not start with a beautiful dashboard.

Recommended order:

```text
1. Report Schema Design
2. Agent Workflow Contract
3. Minimal API response shape
4. Web UI prototype
5. Chart/card polish
6. Metrics Engine
```

Reason:

The product advantage is not visual polish alone. It is trusted, auditable,
source-aware investment research.

## 8. Open Questions Before UI

1. Should the first workspace support only one symbol at a time?
2. Should Chinese company names require confirmation before running research?
3. Should the UI show raw rows, derived summaries, or both?
4. Should Data Confidence be a fixed right-side panel or a section inside the
   report?
5. Should Report Schema be generated by the Agent, by a post-processor, or by a
   dedicated workflow orchestrator?
6. Should `Financial Health` wait for Metrics Engine before adding charts?
7. Should market-wide research use the same workspace or a separate Market
   Overview Workspace?

## 9. Next Step

Next recommended task:

```text
Report Schema + Agent Workflow Design
```

This should still be design-only. It should define the structured output
contract before any UI code is written.
