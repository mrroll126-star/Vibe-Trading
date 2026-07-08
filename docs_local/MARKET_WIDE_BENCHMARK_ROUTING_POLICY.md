# Market-wide Benchmark Routing Policy

## 1. Problem Definition

Pre-tool Symbol Guard is now enabled by default. This protects the project from a serious投研风险: the model silently turning an unclear user target into a ticker and then calling tools on the wrong asset.

That creates one expected edge case. For explicit market-wide questions, the Agent may reasonably need broad benchmark data even when the user did not type each benchmark symbol.

Examples:

* 今天 A 股市场怎么样？
* 美股科技股整体如何？
* 港股市场最近表现如何？
* 当前全市场有什么风险？
* 哪些板块较活跃？

The core question:

How can the Agent use a documented set of market benchmarks for explicit market-wide questions without reopening the risk of silently choosing single-stock targets for the user?

## 2. Core Principle

The agent may use a small, documented benchmark set for explicit market-wide questions, but must label those symbols as system-selected benchmarks rather than user-specified targets.

中文原则：

当用户明确提出全市场、宏观、板块或指数层面问题时，Agent 可以使用一组小而固定、可审计的基准标的，但必须在报告中标注这些标的是系统选择的基准，而不是用户指定标的。

This policy is a narrow exception for market-wide intent. It is not a way to disable Symbol Guard.

## 3. Current Code Discovery

Current market-wide handling:

* `get_stock_news(scope=global)` and `get_stock_news(mode=global|market|all|sector)` can pass Symbol Intent Guard without a single symbol.
* `get_stock_news` broad-market query hints such as 全市场, 宏观, market news, macro news, and sector news are exempt when there is no symbol.
* `get_sector_info(mode=ranking|list|overview)` can pass Symbol Intent Guard when there is no symbol.
* `get_market_data` supports multiple symbols in one call.
* `get_market_data` does not currently have a market-wide benchmark exemption. If it asks for symbols not present in the prompt, Symbol Intent Guard blocks the call.
* Symbol Normalizer can identify common A-share ETFs, A-share stocks, US tickers, and common HK codes. It can mark `000001.SH` as an index only when `prefer_index` context is supplied. It currently treats most explicit `000001.SH` paths as symbol-intent valid, then Asset-type Routing handles whether a tool is suitable.
* Asset-type Routing Guard can allow market data for stock / index / ETF, block unsuitable stock-only tools, and warn for source-dependent ETF news or margin data.
* Reports already have Data Source Summary, Missing Data, Source Warnings, and routing metadata in tool results. They do not yet have Benchmark Selection Summary.

Most likely current false-positive:

* User asks "A 股今天怎么样？"
* Agent calls `get_market_data` for `000001.SH`, `399001.SZ`, `399006.SZ`, `000300.SH`
* Symbol Intent Guard blocks because those symbols were not literally traceable to the user prompt.

## 4. Distinguish Three Intent Types

### 4.1 User-specified Target Intent

The user explicitly asks about a target:

* `600519.SH`
* `510300.SH`
* `QQQ.US`
* `贵州茅台`
* `000001`

Policy:

Continue using Symbol Intent Guard. Do not silently rewrite or replace the user's target. Chinese names and ambiguous symbols should still require confirmation unless an audited resolver policy is introduced.

### 4.2 Market-wide Intent

The user explicitly asks about the market, macro conditions, sectors, industries, or index-level performance:

* A 股今天怎么样？
* 美股整体如何？
* 港股最近风险？
* 全市场新闻
* 板块排行
* 行业表现

Policy:

Allow benchmark policy only when the market-wide intent is explicit and the target market is known.

### 4.3 Ambiguous Intent

The user says something too broad or under-specified:

* 看看市场
* 最近怎么样
* 哪些能买
* 帮我找机会

Policy:

Do not automatically call a benchmark basket. Ask for confirmation, or use non-symbol global tools such as `get_stock_news(scope=global)`, `web_search`, or `get_sector_info(mode=ranking)` where appropriate. Do not turn this into investment advice or stock picking.

## 5. Benchmark Universe MVP

### A-share Market-wide Benchmarks

Recommended MVP:

| Symbol | Meaning | Role |
| --- | --- | --- |
| `000001.SH` | 上证指数 | broad Shanghai market benchmark |
| `399001.SZ` | 深证成指 | broad Shenzhen market benchmark |
| `399006.SZ` | 创业板指 | growth / ChiNext benchmark |
| `000300.SH` | 沪深300 | large-cap cross-market benchmark |

Optional later:

| Symbol | Meaning | Role |
| --- | --- | --- |
| `000905.SH` | 中证500 | mid-cap benchmark |
| `000852.SH` | 中证1000 | small-cap benchmark |

### US Market-wide Benchmarks

Recommended MVP uses ETF proxies because existing US data paths are more likely to support `.US` ETF symbols than caret-prefixed index symbols.

| Symbol | Meaning | Role |
| --- | --- | --- |
| `SPY.US` | S&P 500 ETF proxy | broad US large-cap benchmark |
| `QQQ.US` | Nasdaq-100 ETF proxy | US technology / growth benchmark |
| `DIA.US` | Dow ETF proxy | Dow industrial benchmark |
| `IWM.US` | Russell 2000 ETF proxy | US small-cap benchmark |

Index symbols such as `^GSPC`, `^IXIC`, and `^DJI` should be evaluated later only if providers support them reliably.

### Hong Kong Market-wide Benchmarks

Recommended MVP uses ETF proxies until project support for native Hang Seng index symbols is confirmed.

| Symbol | Meaning | Role |
| --- | --- | --- |
| `02800.HK` | 盈富基金 | Hang Seng proxy |
| `03033.HK` | 恒生科技 ETF proxy | Hong Kong technology proxy |

Native Hang Seng index symbols such as `HSI`, `800000.HK`, or other provider-specific forms require separate provider verification before use.

### Sector / Industry

For sector or industry prompts, prefer:

```text
get_sector_info(mode=ranking)
get_sector_info(mode=list)
get_sector_info(mode=overview)
```

These calls do not require a single benchmark symbol.

## 6. Benchmark Selection Rules

1. If the user explicitly says A 股, 沪深, 中国股市, or A-share market, use the A-share benchmark set.
2. If the user explicitly says 美股, 美国市场, Nasdaq, Dow, S&P, or US technology stocks, use the US benchmark set or the narrower relevant subset.
3. If the user explicitly says 港股 or 香港市场, use the HK benchmark set.
4. If the user says 全市场 but does not specify the market, do not call a cross-market benchmark basket. Ask for the market or use global news / web search.
5. If the user asks for 板块 or 行业排行, prefer `get_sector_info(mode=ranking)` and avoid benchmark symbols.
6. If the user asks for macro news, prefer `get_stock_news(scope=global)` or `web_search`; benchmarks are optional only when the prompt asks for market performance.
7. If the user asks "今天市场表现" and names a market, benchmark symbols may be used.
8. If the user asks for "推荐标的", "哪些能买", or similar trading advice, do not use benchmark policy to produce stock picks or buy/sell advice.

## 7. Guard Interaction

Recommended future order:

1. Detect market-wide intent.
2. If market-wide intent is explicit and the market is known:
   * allow only documented benchmark symbols;
   * mark them as `system_selected_benchmark`.
3. If the prompt is user-specified target intent:
   * use existing Symbol Intent Guard;
   * do not apply benchmark policy.
4. If intent is ambiguous:
   * ask for confirmation or use non-symbol global tools.
5. Apply Asset-type Routing Guard.
6. Apply Data Freshness Guard and report gate.

Important:

Benchmark policy does not bypass Asset-type Routing Guard or Data Freshness Guard.

Example:

`A股今天怎么样？` may allow `get_market_data(000001.SH, 399001.SZ, 399006.SZ, 000300.SH)`, but `get_financial_statements(000001.SH)` should still be blocked because financial statements are company-specific and `000001.SH` is an index benchmark.

## 8. Reporting Requirements

Future reports should include:

```markdown
## Benchmark Selection Summary
```

Required fields:

* Whether the user specified a single target.
* Which benchmarks were system-selected.
* Why each benchmark was selected.
* Market and asset type.
* Data date / timestamp.
* Data source.
* Which benchmark data was missing, stale, or unknown.

Example disclosure:

```text
本报告中的 000001.SH、399001.SZ、399006.SZ、000300.SH 为系统根据「A 股市场」问题选择的市场基准，并非用户指定标的。
```

## 9. MVP Implementation Plan

Future module:

```text
agent/src/symbols/benchmark_policy.py
```

Future pure function:

```python
evaluate_market_wide_benchmark_intent(
    original_prompt: str,
    tool_name: str,
    tool_args: dict,
) -> dict
```

Expected shape:

```json
{
  "decision": "allow_benchmark",
  "market": "cn",
  "benchmarks": ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH"],
  "reason": "explicit_a_share_market_wide_intent",
  "warnings": [],
  "metadata": {
    "benchmark_policy": true,
    "source": "system_selected_benchmark"
  }
}
```

Possible decisions:

* `allow_benchmark`
* `not_market_wide`
* `ask_for_confirmation`
* `block`

Future integration point:

* Inside Symbol Intent Guard, before applying untraceable-symbol block rules; or
* immediately before Symbol Intent Guard as a narrow pre-check that annotates allowed benchmark symbols.

Do not apply benchmark policy to user-specified single-target prompts.

## 10. Acceptance Tests

| Case | Expected |
| --- | --- |
| `prompt=A股今天怎么样` + `get_market_data(000001.SH)` | allow benchmark |
| `prompt=A股今天怎么样` + `get_market_data(399001.SZ)` | allow benchmark |
| `prompt=美股今天怎么样` + `get_market_data(SPY.US)` | allow benchmark |
| `prompt=港股今天怎么样` + `get_market_data(02800.HK)` | allow benchmark |
| `prompt=全市场新闻` + `get_stock_news(scope=global)` | allow without benchmark symbols |
| `prompt=板块排行` + `get_sector_info(mode=ranking)` | allow without benchmark symbols |
| `prompt=看看市场` + `get_market_data(000001.SH)` | ask for confirmation |
| `prompt=贵州茅台怎么样` + `get_market_data(000001.SH)` | block |
| `prompt=000001` + `get_market_data(000001.SZ)` | clarify, not benchmark |
| `prompt=A股今天怎么样` + `get_financial_statements(000001.SH)` | Asset-type Routing block |
| `prompt=美股科技股怎么样` + `get_market_data(QQQ.US)` | allow benchmark |
| `prompt=美股科技股怎么样` + `get_market_data(AAPL.US)` | block or ask for confirmation unless user specified AAPL |

## 11. Relationship to Default Guards

Current defaults:

* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`: on.
* `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD`: on.
* `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`: off.

Benchmark policy is a narrow market-wide exception. It should not require disabling any guard.

## 12. Relationship to a-stock-data

`a-stock-data` remains downstream.

Before adding more A-share data sources, the project should define:

* which A-share benchmarks are allowed;
* when industry ranking is preferred over index benchmarks;
* when ETF proxies are acceptable;
* how source failures and stale benchmark data are shown in reports.

