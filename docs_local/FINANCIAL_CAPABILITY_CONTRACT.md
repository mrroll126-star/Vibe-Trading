# Financial Capability Contract

## 1. Purpose

This contract defines the current financial research capability boundary for
the local Vibe-Trading project.

The purpose is to make clear:

* What financial data the system can directly fetch today.
* What financial metrics can be computed later from raw statements.
* What requests are unsupported and must not be invented by the Agent.
* How data quality and source attribution should be represented.
* How future Research Workspace, Metrics Engine, Valuation Engine, Prompt
  Policy, and Tool Routing work should share the same vocabulary.

This is a product and architecture contract. It is not an implementation plan
for immediate code changes.

## 2. Capability Matrix

| Capability | Status | Source | Notes |
| --- | --- | --- | --- |
| Income Statement | Available | Primary provider + a-stock-data fallback | One of the three raw statements. |
| Balance Sheet | Available | Primary provider + a-stock-data fallback | One of the three raw statements. |
| Cash Flow Statement | Available | Primary provider + a-stock-data fallback | One of the three raw statements. |
| Financial Indicators | Derived | Future Metrics Engine | Not treated as an independent fallback endpoint in the MVP. |
| Valuation Metrics | Partial | Market Data + Metrics Engine | Requires price, market cap, shares outstanding, and accounting fields. |
| Analyst Forecast | Not Available | Future source/module | Must not be fabricated. |
| Peer Comparison | Future | Future universe engine | Needs comparable company set and normalized metrics. |
| ESG / Qualitative | Future | Future external sources | Requires explicit source strategy. |
| Earnings Call / Management Commentary | Future | Future transcript/source integration | Not part of the current financial fallback. |

## 3. Raw Financial Statements Contract

Raw financial statements are source data. They should be fetched, normalized,
and disclosed with provider/source metadata. They are not real-time market
data.

### Income Statement

Supported names:

```text
income
lrb
```

Current source path:

```text
primary: existing Vibe-Trading financial provider
fallback: a-stock-data -> Sina financial report
```

Typical fields:

```text
revenue
operating_revenue
operating_cost
operating_profit
total_profit
net_profit
net_profit_attributable_to_parent
eps
report_date
```

Required output metadata:

```json
{
  "provider": "",
  "source": "",
  "upstream": "",
  "statement_type": "income",
  "period": "",
  "_data_quality": {}
}
```

### Balance Sheet

Supported names:

```text
balance
fzb
```

Current source path:

```text
primary: existing Vibe-Trading financial provider
fallback: a-stock-data -> Sina financial report
```

Typical fields:

```text
total_assets
total_liabilities
shareholders_equity
monetary_funds
accounts_receivable
inventory
report_date
```

Required output metadata:

```json
{
  "provider": "",
  "source": "",
  "upstream": "",
  "statement_type": "balance",
  "period": "",
  "_data_quality": {}
}
```

### Cash Flow Statement

Supported names:

```text
cashflow
llb
```

Current source path:

```text
primary: existing Vibe-Trading financial provider
fallback: a-stock-data -> Sina financial report
```

Typical fields:

```text
operating_cash_flow
cash_received_from_sales
cash_paid_for_goods_services
investing_cash_flow
financing_cash_flow
net_cash_flow
report_date
```

Required output metadata:

```json
{
  "provider": "",
  "source": "",
  "upstream": "",
  "statement_type": "cashflow",
  "period": "",
  "_data_quality": {}
}
```

## 4. Derived Metrics Policy

### Metrics Are Not Data Sources

Financial indicators should not be treated as a separate endpoint by default.
They are derived analytical outputs built from raw statements and, sometimes,
market data.

Example user request:

```text
贵州茅台 ROE 怎么样？
```

The preferred future architecture is:

```text
Financial Statements
        |
        v
Financial Metrics Engine
        |
        v
ROE / margins / growth / efficiency
```

The Agent should not silently pretend that a dedicated indicators endpoint is
available when the system has only income, balance, and cash-flow statements.

### Future Profitability Metrics

Potential future calculations:

* Gross Margin
* Operating Margin
* Net Margin
* ROE
* ROA
* ROIC

Required inputs:

* Income statement.
* Balance sheet.
* Clear period alignment.

### Future Growth Metrics

Potential future calculations:

* Revenue Growth
* Net Profit Growth
* Operating Profit Growth
* EPS Growth
* Cash Flow Growth

Required inputs:

* Same statement type across multiple reporting periods.
* Explicit period labels.

### Future Efficiency Metrics

Potential future calculations:

* Asset Turnover
* Inventory Turnover
* Receivables Turnover
* Cash Conversion indicators

Required inputs:

* Income statement.
* Balance sheet.
* Sometimes cash-flow statement.

## 5. Valuation Capability

Valuation metrics are partial today because they need both financial data and
market data.

Example:

```text
PE = Market Cap / Net Profit
PB = Market Cap / Book Value
```

Required future inputs:

* Latest or chosen-period financial statements.
* Price.
* Market cap or shares outstanding.
* Clear date alignment between market data and financial period.

Current policy:

* The system may discuss historical financial trends from statements.
* The system must not fabricate market cap, PE, PB, target price, fair value,
  or analyst forecast data when those inputs were not retrieved.

## 6. Unsupported Request Policy

The Agent must disclose unsupported capability boundaries instead of
hallucinating.

### Forecasts

Example request:

```text
给我预测明年利润。
```

Current status:

```text
Not Available
```

Expected response pattern:

```text
当前系统没有盈利预测数据源。

可提供：
- 历史收入和利润趋势
- 现金流和资产负债分析
- 已披露财务数据中的风险点

如需要预测，需要未来接入 analyst forecast 或模型预测模块。
```

### Financial Indicators

Example request:

```text
贵州茅台 ROE 如何？
```

Current status:

```text
Derived, not directly available as an independent source.
```

Expected response pattern:

```text
当前系统暂无独立 ROE 数据源。

可以基于：
- 净利润
- 股东权益
- 对应报告期

计算历史 ROE。若缺少任一输入，应说明无法计算。
```

### Peer Comparison

Example request:

```text
茅台和白酒同行相比估值如何？
```

Current status:

```text
Future
```

Expected response pattern:

```text
当前系统尚未定义同行 universe 和统一指标计算口径。
可以先分析单一公司的历史财务表现；同行比较需要后续 universe engine。
```

## 7. Data Quality Contract

Financial data quality should not be described only with market-data
freshness. Financial statements are periodic disclosures.

Current compatible metadata:

```json
{
  "provider": "a_stock_data",
  "source": "sina_financial_report",
  "upstream": "a-stock-data",
  "statement_type": "income",
  "latest_data_date": "2026-03-31",
  "quality_status": "unknown",
  "warnings": []
}
```

Recommended future financial metadata:

```json
{
  "provider": "a_stock_data",
  "source": "sina_financial_report",
  "upstream": "a-stock-data",
  "statement_type": "income",
  "reporting_period": "2026Q1",
  "period_end_date": "2026-03-31",
  "reporting_period_status": "current",
  "warnings": []
}
```

Recommended split:

* `market_data_quality`: latest price, bars, trading-date freshness.
* `financial_data_quality`: reporting period and disclosure recency.
* `news_data_quality`: recency and source timestamps.

### Suggested Financial Period Status

| Status | Meaning |
| --- | --- |
| current | Latest known filing appears appropriate for the current reporting cycle. |
| stale | Latest known filing is unexpectedly old for the company and date. |
| unknown | No reporting period or period end date was extracted. |
| missing | No usable financial statement rows were returned. |

## 8. Tool Routing Rules

The current guardrail direction should remain:

Allowed:

```text
stock
 |
 + income
 + balance
 + cashflow
```

Disallowed:

```text
ETF
 |
 + company financial statements
```

Disallowed:

```text
index
 |
 + company financial statements
```

Policy:

* A-share stocks such as `600519.SH` may use financial-statement tools.
* ETFs such as `510300.SH` should not be treated as operating companies.
* Indices such as `000001.SH` should not use company financial statements.
* US/HK behavior should stay within existing provider compatibility and guard
  rules; do not assume a-stock-data applies outside confirmed A-share stocks.

## 9. Current Limitations

Available now:

* Income statement.
* Balance sheet.
* Cash-flow statement.
* Source Summary for fallback financial data.
* Source Warning when primary provider fails or fallback is used.
* Agent-level consumption of fallback financial data.

Not available now:

* Independent `indicators` endpoint fallback.
* Financial Metrics Engine.
* Valuation Engine.
* Analyst forecasts.
* Peer comparison universe.
* Earnings call transcripts.
* Management guidance.
* ESG/qualitative data source integration.

## 10. Roadmap

### Phase 4: Research Workspace

Goal:

Turn existing data, Agent, guardrails, and source audit into the first usable
research product surface.

Expected consumers:

* Market snapshot.
* Financial statements.
* AI investment memo.
* Data confidence section.

### Phase 5: Metrics Engine

Goal:

Compute derived metrics from raw statements and market data.

Examples:

* ROE.
* Gross margin.
* Net margin.
* Revenue growth.
* Profit growth.
* PE/PB when market cap inputs are available.

### Phase 6: Investment Decision Workflow

Goal:

Support watchlists, portfolio context, thesis tracking, and review workflows.

Boundary:

* No automatic trading.
* No unsupported buy/sell recommendations.
* No fabricated forecasts.

## 11. Product Implication

The next product step should be MVP Research Workspace Design, not another
data-source expansion.

Current foundation:

* Data: available for market data and financial statements.
* Agent: can plan and consume fallback data.
* Guardrails: symbol, asset type, freshness, source disclosure, and report gate.
* Source audit: available through Data Source Summary and warnings.

Missing product layer:

```text
How does a user consume this as a repeatable stock research workflow?
```

Recommended sequence:

```text
Financial Capability Contract
        ↓
MVP Research Workspace Design
        ↓
Report Schema
        ↓
Web UI Prototype
        ↓
Metrics Engine
```
