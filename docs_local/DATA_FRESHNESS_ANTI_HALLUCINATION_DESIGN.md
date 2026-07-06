# Data Freshness & Anti-Hallucination Guardrails Design

Status: design only. No business code changed.

Date: 2026-07-06.

## 1. Problem Definition

Investment research depends on factual data.

In this project, the following are factual data, not writing material for the model to invent:

* Market prices.
* Close prices.
* Intraday prices.
* Price changes and percent changes.
* Trading volume.
* Turnover.
* Fund-flow values.
* Northbound capital flow.
* Financial statement metrics.
* Announcements.
* News.
* Research-report facts and analyst estimates.

These data points have strong time requirements. A correct value from yesterday may be wrong for a question about today. A delayed provider may be acceptable only if the report says it is delayed. A failed provider must be disclosed instead of hidden.

The core product risk is simple:

* If the LLM cannot get today's data, it may still generate a plausible-looking close price, percent change, volume, or fund-flow number.
* Plausible-looking fabricated data is more dangerous than an explicit error.
* For short-term research, this can make the product misleading or unusable.

Therefore:

* Missing data must be marked as missing.
* Stale data must be marked as stale.
* Unknown freshness must be marked as unknown.
* Source failures must be disclosed.
* Anti-hallucination guardrails must be designed and implemented before `a-stock-data` is integrated into production research workflows.

## 2. Highest Principle

LLM must not invent market data.

中文原则：

模型不得编造行情、价格、成交量、成交额、涨跌幅、财务指标、资金流、公告、新闻、研报等事实性数据。

## 3. Current Risk Assessment

This assessment is based on read-only inspection of current tool, loader, Agent loop, trace, session, and run code.

### 3.1 Current Tools With Date / Timestamp Fields

| Tool | Current date/time fields found | Notes |
| -- | -- | -- |
| `get_market_data` | Loader rows usually carry date/index fields after `df.reset_index()` | Field name depends on loader dataframe index/columns. No unified `data_date` or `freshness_status`. |
| `get_stock_news` | A-share articles include `published`; articles also include media `source` | US/HK path returns Yahoo instrument matches, not news articles. Matches do not represent news timestamps. |
| `get_stock_profile` | Some sections include `end_date` or `report_date` | No top-level `data_timestamp`; Yahoo profile path can fail in this local environment. |
| `get_research_reports` | Reports include `publish_date`; consensus EPS is forward-year data | THS consensus is best-effort and may silently degrade to empty consensus records. |
| `get_fund_flow` | Rows include `timestamp`; daily rows are dates and minute rows include date/time | No explicit `requested_at`, freshness status, or realtime/delayed flag. |
| `get_margin_trading` | Rows include `trade_date` | Daily exchange-published data, no explicit freshness classification. |
| `get_shareholder_count` | Rows include `end_date` | Periodic disclosure, not intraday data. |
| `get_sector_info` | Ranking data is described as today's board ranking, but inspected tool envelope has no unified timestamp | Membership mode is taxonomy-like; ranking mode needs freshness metadata. |
| `get_northbound_flow` | History rows include `trade_date`; realtime payload has no top-level timestamp in current envelope | Market-wide flow should disclose if realtime fields are missing or stale. |
| `get_block_trades` | Records include `trade_date`; request window is based on local current date | No top-level freshness status. |
| `get_financial_statements` | Period rows include `REPORT_DATE`-derived fields | Financial statement data is periodic and should be treated separately from live market data. |

### 3.2 Tools Without Clear Top-Level Freshness Metadata

Most current tools do not return a standard top-level freshness block.

Common missing fields:

* `requested_at`
* `data_date`
* `data_timestamp`
* `freshness_status`
* `is_realtime`
* `is_delayed`
* `delay_minutes`
* `source_success`
* `source_error`
* `row_count`
* `warnings`

### 3.3 Source / Provider Coverage

Several tools return top-level `source`, for example:

* `get_stock_news`: `eastmoney` or `yahoo`.
* `get_stock_profile`: `yahoo`.
* `get_research_reports`: `eastmoney+ths`.
* `get_fund_flow`: `eastmoney`.
* `get_margin_trading`: `eastmoney`.
* `get_shareholder_count`: `eastmoney`.
* `get_sector_info`: `eastmoney`.
* `get_northbound_flow`: `eastmoney`.
* `get_block_trades`: `eastmoney`.
* `get_financial_statements`: `sec_edgar` or `eastmoney`.

`get_market_data` currently groups by detected loader source internally, but the returned JSON is keyed by symbol and `_unresolved`; it does not expose a per-symbol `source` / `provider` summary in a standardized wrapper.

### 3.4 Failure Recording

Current Agent loop behavior:

* Tool calls are written to trace as `tool_call` records.
* Tool results are written to trace as `tool_result` records.
* Tool results include status `ok` or `error` based on `_is_tool_success`.
* Large tool results may be offloaded to sidecar files.
* Tool result previews are emitted to Web UI / SSE.
* Tool timeout is converted into a JSON error.

This means failures can enter trace. However, there is no guarantee that the final report will prominently disclose all source failures.

### 3.5 Final Report Risk

Current final report behavior:

* The Agent receives tool results as conversation messages.
* The LLM decides how to write the final answer.
* The final answer is stored as `content`.
* A run can be marked success if `final_content` exists.

Risk:

* If a data tool fails, the model may still write a normal-looking answer.
* If data is stale, the model may not identify it as stale.
* If the tool result has no timestamp, the model may assume it is current.
* If only a preview is easy to see in UI, source failures may be under-disclosed to the user.
* Current reports do not enforce a hard distinction between data facts and model interpretation.

### 3.6 Highest-Risk Scenarios

Highest risk:

* Today's close.
* Intraday trend.
* Latest price.
* Today's percent change.
* Today's turnover and volume.
* Today's fund flow.
* Northbound flow.
* Latest news.
* Latest announcements.
* Latest research reports.
* Financial metrics when the period is not disclosed.

These questions should trigger freshness checks before a normal research report is allowed.

## 4. Data Facts vs Model Interpretation

Every research report that uses market data should separate:

* Data Facts
* Model Interpretation
* Missing Data
* Source Failures
* Assumptions
* Not Investment Advice

Rules:

* Data Facts can only come from tool-returned data.
* Model Interpretation must be based on Data Facts.
* Missing Data must list data that was requested or needed but not obtained.
* Source Failures must list failed, skipped, empty, delayed, or timestamp-unknown sources.
* Assumptions must be clearly labeled as assumptions or inference.
* The model must not write assumptions as facts.
* If a report uses prior trading-day data, it must say so.
* If data freshness is unknown, it must say freshness is unknown.

Recommended report sections:

```text
## Data Facts
## Model Interpretation
## Missing Data
## Source Failures
## Assumptions
## Not Investment Advice
```

## 5. Data Freshness Metadata

All data tools should eventually return or be wrapped with a standard metadata block.

Recommended fields:

| Field | Meaning |
| -- | -- |
| `raw_input` | User or tool-call input before normalization. |
| `normalized_symbol` | Project-standard symbol after normalization, if available. |
| `symbol` | Symbol actually sent to the data provider. |
| `market` | Market classification such as `CN`, `US`, `HK`, `global`, or `unknown`. |
| `asset_type` | Stock, ETF, index, fund, crypto, or unknown. |
| `tool_name` | Tool that produced the data. |
| `source` | User-facing data source label, such as `eastmoney`, `yahoo`, `tencent`. |
| `provider` | Implementation provider or loader name, if different from `source`. |
| `data_date` | Trading date or disclosure date represented by the data. |
| `data_timestamp` | Exact timestamp when provider says the data was updated. |
| `requested_at` | Local timestamp when Vibe-Trading requested the data. |
| `freshness_status` | One of `fresh`, `stale`, `unknown`, `missing`. |
| `is_realtime` | Whether the provider claims realtime data. |
| `is_delayed` | Whether the data is known to be delayed. |
| `delay_minutes` | Known delay in minutes, or null. |
| `source_success` | Boolean success state for the provider call. |
| `source_error` | Structured error summary if the provider failed. |
| `row_count` | Number of rows/items returned. |
| `confidence` | Confidence in symbol match and freshness interpretation. |
| `warnings` | Human-readable warnings, such as stale data or unknown timestamp. |

Recommended wrapper shape:

```json
{
  "ok": true,
  "tool_name": "get_market_data",
  "request": {
    "raw_input": "600519",
    "normalized_symbol": "600519.SH",
    "requested_at": "2026-07-06T15:05:00+08:00"
  },
  "sources": [
    {
      "source": "tencent",
      "provider": "tencent",
      "source_success": true,
      "source_error": null,
      "row_count": 1,
      "data_date": "2026-07-06",
      "data_timestamp": "2026-07-06T15:00:00+08:00",
      "freshness_status": "fresh",
      "is_realtime": false,
      "is_delayed": false,
      "delay_minutes": null,
      "warnings": []
    }
  ],
  "data": {}
}
```

## 6. Freshness Rules By Market

### A-Share

Recommended rules:

* Intraday trading-day data must carry today's date and a provider timestamp.
* Post-close analysis must confirm the data date is the current trading day.
* If only the previous trading day is available, mark `freshness_status=stale`.
* If trading calendar is unavailable, mark `freshness_status=unknown`.
* Intraday realtime status cannot be assumed from a daily bar.
* Do not infer today's close from historical daily bars.
* Do not calculate today's percent change unless today's price and comparison close are both available and dated.
* Fund-flow reports must state whether the latest row is daily or minute-level.

### US Stocks

Recommended rules:

* Timezone must be explicit. US market dates should not be compared against China local date without conversion.
* Premarket, regular session, after-hours, and post-close data should be distinguished.
* Close-price claims must confirm the market date and session.
* Yahoo/yfinance profile or chart failures must be disclosed.
* Delayed data must be marked `delayed`.
* If a provider returns only prior-session data during premarket, the report must say it is prior-session data.

### Hong Kong Stocks

Recommended rules:

* Hong Kong trading day and lunch break must be considered.
* Close-price claims must confirm the market date.
* HK symbol conversion, such as `00700.HK` to Yahoo `0700.HK`, must not erase freshness metadata.
* If a provider returns stale daily bars, mark stale rather than treating the data as current.

## 7. Source Failure Disclosure

Every provider failure should enter:

* Trace.
* Report source summary.
* Missing data section.

Examples:

* `yfinance failed: TLS error`
* `Tushare skipped: token missing`
* `eastmoney returned empty rows`
* `baostock unavailable: dependency missing`
* `local provider skipped: data bridge not configured`

The final report should tell the user:

* Which sources succeeded.
* Which sources failed.
* Which sources were skipped.
* Which sources returned empty data.
* Which conclusions are therefore unreliable or unavailable.

Recommended report source summary:

```text
## Data Source Summary

Succeeded:
- get_market_data / tencent: returned 1 latest daily row for 600519.SH, data_date=2026-07-06.

Failed:
- yfinance: TLS connection reset.
- tushare: token missing.

Missing:
- No verified current-day fund-flow data.

Freshness:
- Market data: fresh.
- Fund flow: missing.
- News: timestamp unknown.
```

## 8. Report Gate Design

The system should classify time-sensitive questions before allowing a normal report.

Time-sensitive terms include:

* 今日
* 今天
* 盘中
* 实时
* 收盘
* 最新
* 当前
* 刚刚
* 当日涨跌幅
* 今日成交额
* 今日资金流

If a question is time-sensitive, the system must first check whether critical data is fresh.

Critical data examples:

* Today's market data for price/close/change/volume questions.
* Today's or latest timestamped fund-flow data for fund-flow questions.
* Latest timestamped news items for news questions.
* Latest announcement data for announcement questions.
* Latest northbound data for northbound-flow questions.

If critical data is missing:

* Do not generate a normal factual research conclusion.
* Output a Data Insufficient Report.
* Tell the user which data is missing.
* Tell the user which sources failed or were skipped.
* Offer a safer alternative such as historical overview based on the latest available dated data.

Example:

```text
我没有获取到 2026-07-06 的 600519.SH 当日收盘价，因此不能分析今日收盘表现。
当前仅能基于最近可用的历史数据做概览。
```

## 9. Prompt / System Instruction Rules

Future Agent system prompt should include rules like:

* Use only tool-returned data for factual market claims.
* If data is missing, say it is missing.
* Never fabricate prices, volumes, turnover, dates, financial metrics, news, announcements, or research-report facts.
* Separate facts from interpretation.
* Cite tool and source names where possible.
* Disclose source failures.
* Do not infer today's close from historical data.
* Do not fill missing numeric fields with estimates.
* If freshness is unknown, say freshness is unknown.

Suggested Chinese system prompt block:

```text
你是一个投研 Agent。你必须严格区分“工具返回的数据事实”和“基于事实的分析判断”。

你不得编造行情、价格、成交量、成交额、涨跌幅、财务指标、资金流、公告、新闻、研报等事实性数据。

凡是事实性市场数据，必须来自工具返回结果；如果工具没有返回、返回为空、返回失败、数据过期、延迟或时间戳未知，你必须明确说明“未获取到”“数据过期”“数据延迟”或“新鲜度未知”，不得用估计值补全。

当用户询问“今天、今日、盘中、实时、最新、当前、收盘、当日涨跌幅、今日成交额、今日资金流”等强时效问题时，你必须先确认关键数据的新鲜度。若关键数据缺失，不得生成正常事实性结论，应输出数据不足说明，并列出缺失数据和失败数据源。

报告必须包含或清晰表达：Data Facts、Model Interpretation、Missing Data、Source Failures、Assumptions、Not Investment Advice。推测必须标注为推测，不能写成事实。
```

## 10. Implementation Phases

### Phase A: Design Only

Current phase.

Deliverables:

* This design document.
* ADR.
* Roadmap, backlog, next-task priority updates.

### Phase B: Freshness Wrapper For `get_market_data`

Goal:

* Add a wrapper around `get_market_data` results.
* Include `requested_at`, per-symbol source summary, row count, latest data date, and freshness status.
* Do not change provider fallback order.
* Do not add new data sources.

Why first:

* Price/volume/close/change claims are the most common hallucination risk.
* `get_market_data` is the central market-data path.

### Phase C: Source Summary In Report

Goal:

* Add Data Source Summary, Missing Data, and Source Failures to final reports.
* Ensure failed tools are visible in the user-facing answer, not only in trace.

### Phase D: Report Gate For Time-Sensitive Questions

Goal:

* Detect strong time-sensitive asks.
* Require fresh critical data before normal factual reports.
* Return Data Insufficient Report when data is missing/stale/unknown.

### Phase E: Extend To A-Share Tools

Extend metadata and failure disclosure to:

* `get_fund_flow`
* `get_northbound_flow`
* `get_research_reports`
* `get_stock_news`
* `get_financial_statements`
* `get_margin_trading`
* `get_shareholder_count`
* `get_sector_info`
* `get_block_trades`

### Phase F: Integration With `a-stock-data` Adapter

Before `a-stock-data` enters production research workflows:

* The adapter must implement the freshness contract.
* The adapter must return source success/failure metadata.
* The adapter must expose data date/timestamp where available.
* The report gate must treat adapter failures like any other provider failure.

## 11. Acceptance Test Design

| Scenario | Input | Data State | Expected Behavior |
| -- | -- | -- | -- |
| Today's close succeeds | “分析 600519.SH 今日收盘表现” | Market data has today's date and close | Normal report allowed; cites source/date. |
| Today's data missing | “600519.SH 今天涨跌幅是多少？” | No row for current trading day | Data Insufficient Report; no invented price/change. |
| Only previous trading day exists | “600519.SH 今日走势如何？” | Latest row is prior trading day | Mark stale; offer historical overview only. |
| All providers fail | “AAPL.US 最新走势” | All market-data providers failed | Report source failures; no market-data conclusion. |
| One provider succeeds, one fails | “SPY.US 最新走势” | Yahoo succeeds, yfinance fails | Use successful source; disclose yfinance failure. |
| Delayed data | “AAPL.US 实时价格” | Provider says delayed | Mark delayed; do not call it realtime. |
| Fund flow failure | “600519.SH 今日资金流如何？” | fund-flow tool fails | Missing fund-flow section; disclose failure. |
| News empty | “600519.SH 最新新闻” | news returns empty articles | Say no news retrieved; do not invent headlines. |
| yfinance TLS failure | “AAPL.US 基本面和走势” | Yahoo profile/yfinance TLS fails | Disclose TLS failure; use only other successful data. |
| Tushare token missing | A-share data task | Tushare skipped due to missing token | Mark skipped; no mysterious failure. |
| Today percent change without today data | “今天涨跌幅” | Only historical data | Refuse exact today change; explain missing data. |
| Latest announcement empty | “最新公告” | announcement source empty/unavailable | Say announcement data not retrieved. |
| Northbound failure | “今日北向资金” | northbound tool fails | No invented northbound number; disclose failure. |
| Timestamp unknown | “当前价格” | Tool returns value but no timestamp | Mark freshness unknown; do not call it current. |
| LLM attempts unsupported numeric claim | Any time-sensitive prompt | Tool did not return value | Prompt/gate blocks or forces correction before final report. |

Markets covered:

* A-share.
* US stocks.
* Hong Kong stocks.

Report types covered:

* Intraday/current-day market summary.
* Post-close daily review.
* Fund-flow review.
* News/announcement review.
* Financial/fundamental review.

## 12. Priority Decision

Data Freshness & Anti-Hallucination Guardrails must be implemented before `a-stock-data` adapter is integrated into production workflows.

中文：

在 `a-stock-data` 接入生产工作流之前，必须先实现数据新鲜度和防数据幻觉护栏。

Reason:

Adding more data sources without freshness and failure guardrails can make the product look more capable while still allowing the LLM to fabricate missing facts. The guardrail layer should become the contract every future provider, including `a-stock-data`, must satisfy.
