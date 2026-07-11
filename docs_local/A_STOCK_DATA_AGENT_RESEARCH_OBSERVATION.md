# a-stock-data Agent Research Observation

## 1. Purpose

This document records the first controlled Agent-level observation for the
`a-stock-data` financial fallback.

The goal was to answer one question:

Can the original Agent workflow discover `get_financial_statements`, consume
the feature-flagged `a-stock-data` fallback, and produce an auditable report
without Web UI or provider-chain changes?

## 2. Scope

Included:

* One controlled AgentLoop run.
* Only `get_financial_statements` exposed to the Agent.
* Primary financial provider forced to fail in-process.
* `a-stock-data` fallback enabled only inside the script process.
* Live Sina fallback requests for `600519.SH`.

Excluded:

* No Web UI.
* No full product workflow.
* No provider-chain changes.
* No loader changes.
* No default feature flag changes.
* No fund-flow, news, or research-report adapter.
* No `agent/.env` content read or printed.

## 3. Script

Added:

```text
scripts/observe_agent_financial_fallback_research.py
```

Command:

```bash
.venv/bin/python scripts/observe_agent_financial_fallback_research.py --timeout 15 --max-iterations 8 --output-dir local_reports
```

The JSON output was written to ignored `local_reports` and was not committed.

## 4. Runtime Flags

The script set these values only inside its process:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1
VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY=0
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

The repository default remains:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0
```

## 5. Prompt

```text
分析贵州茅台（600519.SH）的最新财务情况，包括收入、利润、资产负债和现金流，并说明主要风险。只使用实际获取到的数据，不要估算。请说明数据来源和报告期；如果没有拿到实时或当天财务数据，请明确说明财务报表不是实时数据。
```

## 6. Result

Run:

```text
run_id: 20260711_222201_15_854f55
status: success
iterations: 2/8
```

Agent tool calls:

```text
get_financial_statements 600519.SH income
get_financial_statements 600519.SH balance
get_financial_statements 600519.SH cashflow
get_financial_statements 600519.SH indicators
```

Fallback source:

```text
provider: a_stock_data
source: sina_financial_report
upstream: a-stock-data
latest_data_date: 2026-03-31
```

Warnings:

```text
primary_financials_unavailable
a_stock_data_fallback_used
a_stock_data_fallback_failed
```

The `a_stock_data_fallback_failed` warning came from the Agent asking for
`indicators`, which is intentionally not supported by the current Sina
statement mapping.

## 7. Acceptance Checks

Passed:

* Agent called `get_financial_statements`.
* Primary financial provider was forced to fail.
* Fallback was used for financial-statement data.
* Data Source Summary appeared in the final answer.
* Source Warnings appeared in the final answer.
* The answer mentioned the source and report date.
* The answer disclosed that financial reports are not real-time data.
* No Symbol Clarification block occurred for explicit `600519.SH`.
* No benchmark policy path was involved.
* No asset-type routing block occurred.

Observed issue:

* The Agent asked for `indicators`, but `a-stock-data` MVP currently supports
  only `income`, `balance`, and `cashflow`.

## 8. Business Interpretation

This observation shows the first complete controlled chain:

```text
Agent reasoning
-> get_financial_statements
-> forced primary failure
-> a-stock-data Sina fallback
-> _data_quality
-> Data Source Summary / Source Warnings
-> final report
```

This does not mean the adapter should be default-on. It means the optional
fallback path is now observable at Agent level and can be tested further before
Web UI exposure.

## 9. Next Recommendations

1. Keep `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0` by default.
2. Add a policy decision for `indicators`: either map it to a supported source
   later or teach the Agent/report to say indicators are unavailable.
3. Do one Web UI observation only after the CLI Agent observation remains
   stable and the user explicitly approves.
