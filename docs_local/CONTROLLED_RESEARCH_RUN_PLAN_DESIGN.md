# Controlled Research Run Plan Design

## 1. Purpose

This document defines a controlled real Agent research run for validating the
next product-critical pipeline:

```text
Research Intent
  -> Tool Execution
  -> Complete Trace
  -> Structured Research Schema
```

This is a design document only. It does not run AgentLoop, call live data,
modify providers, modify loaders, modify Web UI, or write production schema
artifacts.

The immediate reason for this design is that the historical trace observation
proved real trace readability and schema construction, but the selected trace
only contained financial `indicators`. It did not contain the complete
financial statement set needed by the MVP Research Workspace:

* income statement
* balance sheet
* cash flow statement

## 2. Controlled Run Scope

First controlled target:

```text
300750.SZ
```

Why `300750.SZ`:

* It is an explicit A-share stock symbol.
* It avoids symbol ambiguity.
* It is a real company, not an index or ETF.
* It is suitable for the A-share financial fallback path.
* It was already present in earlier trace observations, which makes before/after
  comparison easier.

Out of scope for the first controlled run:

* multiple stocks
* portfolio analysis
* Web UI run
* benchmark policy validation
* valuation engine
* target price
* forecast generation
* trading recommendation
* production `research_schema.json` artifact writing

## 3. Research Intent Contract

Controlled user intent:

```text
Analyze 300750.SZ. Include current market snapshot, income statement, balance
sheet, cash flow statement, recent news, research report availability, sector
context, key risks, and data source confidence. Do not provide buy/sell advice.
Use only data actually retrieved by tools. If data is missing, state it as
missing.
```

Expected normalized research intent:

```json
{
  "symbol": "300750.SZ",
  "market": "A-share",
  "asset_type": "stock",
  "analysis_type": "single_stock_research",
  "required_capabilities": [
    "market_snapshot",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "news",
    "research_reports",
    "sector_context",
    "data_confidence"
  ],
  "excluded_capabilities": [
    "target_price",
    "buy_sell_recommendation",
    "portfolio_action",
    "unsupported_forecast"
  ]
}
```

The run should not let the final report invent unsupported capabilities. If a
capability is not available, it should appear as missing or limited.

## 4. Tool Requirement Matrix

| Capability | Required tool(s) | Required output | Complete if | Partial if | Failed if |
| --- | --- | --- | --- | --- | --- |
| Symbol contract | Symbol guard / existing symbol handling | explicit `300750.SZ`, market, asset type | symbol accepted as A-share stock | symbol accepted but asset type unknown | symbol rejected or ambiguous |
| Market snapshot | `get_market_data` | price/trend fields and `_data_quality` | market data exists with quality metadata | market data exists but date/quality incomplete | no market data |
| Income statement | `get_financial_statements(statement_type="income")` | rows, provider/source, period/date, `_data_quality` | rows exist | rows exist but quality metadata incomplete | no rows |
| Balance sheet | `get_financial_statements(statement_type="balance")` | rows, provider/source, period/date, `_data_quality` | rows exist | rows exist but quality metadata incomplete | no rows |
| Cash flow | `get_financial_statements(statement_type="cashflow")` | rows, provider/source, period/date, `_data_quality` | rows exist | rows exist but quality metadata incomplete | no rows |
| News | `get_stock_news` | recent news items or explicit no-data result | news exists with source/date | no news but tool reports clean no-data | tool fails without useful warning |
| Research reports | `get_research_reports` | report list or explicit no-data result | reports exist with source/date | no reports but tool reports clean no-data | tool fails without useful warning |
| Sector context | `get_sector_info` | sector or industry context | sector context exists | sector context missing but non-core analysis remains possible | tool failure causes unsupported sector claims |
| Data confidence | report data-quality metadata | provider/source/date/status/warnings | all core data has quality metadata | non-core data lacks quality metadata | core data lacks source/quality |

## 5. Required Tool Calls

Minimum expected tool call set:

```text
get_market_data(symbol="300750.SZ")
get_financial_statements(symbol="300750.SZ", statement_type="income")
get_financial_statements(symbol="300750.SZ", statement_type="balance")
get_financial_statements(symbol="300750.SZ", statement_type="cashflow")
get_stock_news(symbol="300750.SZ")
get_research_reports(symbol="300750.SZ")
get_sector_info(symbol="300750.SZ")
```

Optional but useful:

```text
get_fund_flow(symbol="300750.SZ")
get_margin_trading(symbol="300750.SZ")
get_shareholder_count(symbol="300750.SZ")
```

For the first controlled run, optional tools should not determine schema
completion. They may enrich risks, but must not be required.

## 6. Completion Criteria

### Complete

The run is schema-complete if all are true:

* verified explicit symbol: `300750.SZ`
* asset type is stock
* market snapshot exists
* income statement exists
* balance sheet exists
* cash flow statement exists
* data confidence exists for market and financial data
* trace includes tool calls and tool results for the required tools
* final answer exists
* structured schema can be built with no missing core sections

Non-core missing news or research reports may still be acceptable if the schema
records them as unavailable.

### Partial

The run is schema-partial if any are true:

* news missing but clearly disclosed
* research reports missing but clearly disclosed
* sector context missing but clearly disclosed
* some financial quality metadata is incomplete, while rows exist
* final answer exists but lacks useful memo content

Partial runs can still be useful for improving trace collection and schema
builder behavior.

### Failed

The run is schema-failed if any are true:

* symbol is not verified
* symbol is ambiguous
* asset type is not stock
* market data missing with no clear warning
* all core financial data missing
* no tool results are present in trace
* trace cannot be read
* schema builder cannot produce required top-level sections
* final report invents unsupported data instead of recording missing data

## 7. Trace Validation Contract

The completed run trace must contain enough data for post-processing without
rerunning tools.

Required event fields:

```text
type
timestamp or event order
tool name
tool arguments or enough symbol/type context
tool status
tool result or result_path
final answer content or content_path
```

Required trace properties:

* Tool results are recorded after tool calls.
* Offloaded tool results can be resolved.
* Failed tool calls include structured status/error.
* Tool result payloads retain provider/source/date/quality metadata.
* The trace can be processed without reading `.env` or calling external APIs.

If a tool result is too large and offloaded, the observation path should use:

```text
TraceWriter.read(..., resolve_offloads=True)
```

If a tool result does not include enough context for `trace_collector`, the
minimal future fix should be adding metadata to trace events, not rerunning
tools.

## 8. Schema Completeness Report

Future observation output should include:

```json
{
  "schema_status": "complete | partial | failed",
  "symbol": "300750.SZ",
  "missing_capabilities": [],
  "warnings": [],
  "tool_coverage": {
    "get_market_data": "present | missing | failed",
    "get_financial_statements:income": "present | missing | failed",
    "get_financial_statements:balance": "present | missing | failed",
    "get_financial_statements:cashflow": "present | missing | failed",
    "get_stock_news": "present | missing | failed",
    "get_research_reports": "present | missing | failed",
    "get_sector_info": "present | missing | failed"
  },
  "data_confidence": {
    "market_data": {
      "provider": "",
      "source": "",
      "date": "",
      "status": ""
    },
    "financial_data": {
      "provider": "",
      "source": "",
      "reporting_period": "",
      "status": ""
    }
  }
}
```

This completeness report should be separate from the final investment memo. It
is an audit object that tells the product whether the schema is safe to render.

## 9. Data Confidence Requirements

Core conclusions must not be created unless their source data exists.

Market conclusions require:

* `get_market_data` result
* provider/source
* date or timestamp
* data quality status

Financial conclusions require:

* income statement rows
* balance sheet rows
* cash flow rows
* provider/source
* reporting period
* warnings, including fallback usage

AI memo content may interpret the data, but cannot invent:

* price
* revenue
* profit
* assets
* liabilities
* cash flow
* provider
* source
* report date

## 10. Controlled Run Boundary

The first real validation should be executed only after user confirmation.

It should use:

```text
symbol: 300750.SZ
mode: single-stock controlled research
feature flags:
  VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1
  VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
  VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1
  VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0
  VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY=0
```

Reasoning:

* The symbol is explicit, so symbol normalizer is unnecessary.
* The symbol and asset guards should remain active.
* Benchmark policy is unrelated to a single-stock research run.
* a-stock-data fallback is needed to improve financial statement coverage.

The first execution should not use Web UI. It should prefer the same backend/API
or CLI path that produces a durable run/session trace, but the exact entrypoint
should be selected only after checking the current service state.

## 11. Post-run Observation Plan

After the controlled run finishes:

1. Identify the generated `run_id` or `session_id`.
2. Do not inspect raw tool rows in chat.
3. Run:

```bash
.venv/bin/python scripts/observe_real_trace_to_schema.py \
  --run-id <run_id> \
  --symbol 300750.SZ \
  --output-dir local_reports
```

Or, if the run is session-scoped:

```bash
.venv/bin/python scripts/observe_real_trace_to_schema.py \
  --session-id <session_id> \
  --symbol 300750.SZ \
  --output-dir local_reports
```

4. Confirm the compatibility summary.
5. Do not write production `research_schema.json` until this observation passes.

## 12. Next Stage Recommendation

Next task:

```text
Controlled Real Agent Research Run
```

That task should:

* run exactly one controlled Agent research task
* use explicit `300750.SZ`
* request income, balance, and cash flow
* keep Web UI out of scope
* write observation output only to ignored `local_reports`
* update docs with the resulting trace/schema compatibility

Only after that proof should the project design production schema artifact
writing.
