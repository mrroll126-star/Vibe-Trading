# Minimal Research Task

Status: prepared only. Do not run until the user manually adds an LLM provider key or configures Ollama and explicitly approves the test.

## 1. Goal

Verify that Vibe-Trading can complete one real, low-cost research workflow after LLM provider setup.

This test should answer:

* Can the Agent start a task?
* Can it call at least one market-data source?
* Can it produce a short research answer/report?
* Can the result be seen in the Web UI or CLI?
* Are there obvious errors in logs?

This is not a trading test.

## 2. Boundaries

Do not:

* Enable shell tools.
* Connect trading/broker execution.
* Add `a-stock-data`.
* Modify provider chains.
* Run a large swarm.
* Ask for buy/sell instructions.

Keep:

* `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* `agent/.env` ignored by Git.
* `API_AUTH_KEY` configured.

## 3. Recommended Test Target

Use one simple US symbol first:

* `AAPL`
* or `SPY`

Reason:

* US smoke test already showed direct Yahoo, Sina, and Eastmoney can return basic AAPL/MSFT data in this environment.
* `yfinance` is currently degraded, but it is not the only possible US source.
* AAPL/SPY are common, liquid, and easy to sanity-check.

Optional later A-share target:

* `600519`

Only use it after the basic US workflow works.

## 4. Recommended Prompt

Short first prompt:

```text
请分析 AAPL 最近走势和主要风险，用中文输出一份简短研究摘要。不要给出买卖建议。
```

Alternative ETF prompt:

```text
请生成 SPY 的简短市场概览，说明近期走势、可能风险和需要继续跟踪的数据。不要给出买卖建议。
```

## 5. Start Commands

Backend:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Open:

```text
http://127.0.0.1:5899
```

CLI alternative:

```bash
.venv/bin/vibe-trading run -p "请生成 SPY 的简短市场概览，说明近期走势、可能风险和需要继续跟踪的数据。不要给出买卖建议。"
```

## 6. Validation Checklist

Pass criteria:

* Backend starts without LLM preflight error for the configured provider.
* Frontend opens.
* Agent run starts from Web UI or CLI.
* The run completes or produces a clear partial result.
* The result includes a concise analysis.
* The answer avoids direct buy/sell instructions.
* The run is visible in the Web UI run/session list.
* No secret key is printed in logs.

Data-source criteria:

* At least one market-data call succeeds.
* If `yfinance` fails, the run still has a chance to use another provider or should report the data-source failure clearly.

## 7. Common Failure Causes

LLM key error:

* Provider key is missing, expired, mistyped, or pasted with spaces.
* Wrong `LANGCHAIN_PROVIDER`.
* Wrong `LANGCHAIN_MODEL_NAME`.
* Wrong base URL.

Provider data failure:

* Network request failed.
* yfinance TLS issue appears again.
* Provider rate limit or empty result.
* Symbol format mismatch.

API auth issue:

* Browser has the wrong API auth key stored.
* Backend was not restarted after editing `agent/.env`.
* `API_AUTH_KEY` was changed locally but the Web UI still has the old value.

Frontend/backend connection issue:

* Backend is not running on `127.0.0.1:8899`.
* Frontend `VITE_API_URL` points to the wrong backend.
* Port `5899` or `8899` is occupied.

Shell tools:

* Should remain disabled.
* If a task says it needs shell tools, stop and ask the user before changing anything.

## 8. Suggested First Run Report

After the first approved run, record:

* Provider used.
* Model used.
* Prompt used.
* Whether the run completed.
* Whether data was fetched.
* Any provider/data errors.
* Whether Web UI showed the result.
* Whether logs exposed any secret. They should not.

## 9. First Run Result

Date: 2026-07-05.

Prompt:

```text
请生成 SPY 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。
```

Run method:

```bash
.venv/bin/vibe-trading run -p "请生成 SPY 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。"
```

Result:

* Status: success.
* Run ID: `20260705_162441_99_2b6f81`.
* Run directory: `agent/runs/20260705_162441_99_2b6f81`.
* Runtime: about 1 minute 12 seconds.
* Provider: DeepSeek.
* Model: `deepseek-v4-pro`.
* LLM calls: 5.
* Total provider-reported tokens: 169,015.
* Output language: Chinese.
* The final answer included a clear statement that it was not investment advice.

Generated report summary:

* SPY was described as near an upper range with key resistance around 750 and support around 740.
* The answer highlighted technology/semiconductor leadership, macro/geopolitical context, inflation and Fed policy risk, concentration risk, and technical overheat risk.
* It provided a scenario table and follow-up watchlist.
* It avoided direct buy/sell instructions.

Data/tool observations:

* Agent task started and completed.
* Trace shows tool calls including `get_market_data`, `get_stock_profile`, and `get_stock_news`.
* `get_market_data` returned `_unresolved` for `SPY`; likely because the tool expected a suffix such as `SPY.US`.
* `get_stock_news` reported unsupported market for `SPY`; expected suffixes include `SH`, `SZ`, `BJ`, `US`, `HK`.
* Yahoo profile/options paths hit SSL or connection-reset failures.
* The known yfinance/curl TLS issue still appears in preflight and remains unresolved.

Interpretation:

* LLM provider verification passed.
* Native Vibe-Trading Agent workflow can run end-to-end with DeepSeek.
* The first prompt should use explicit project-style symbols next time, for example `SPY.US` or `AAPL.US`, to improve data tool routing.
* Data-source reliability still needs follow-up; do not treat this first report as a data-quality benchmark.

Next minimal rerun recommendation:

```text
请生成 SPY.US 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。
```

## 10. Phase 0 Conclusion

The minimal native research workflow is verified.

Conclusion:

* DeepSeek can power the Agent.
* The Agent can start and complete a research task.
* The Agent can call data tools.
* The Agent can generate a readable Chinese research summary.
* The output can respect the no-buy/sell-advice boundary.

Remaining caveat:

* Symbol normalization and data-source reliability need Phase 1 work before this can be treated as a robust research production workflow.
