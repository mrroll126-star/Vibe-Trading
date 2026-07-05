# Phase 0 Bootstrap Summary

Status: completed on 2026-07-05.

## 1. Phase 0 Goal

Phase 0 was the bootstrap and proof-of-life phase for a local, auditable, long-term-maintained Vibe-Trading research project.

Goals:

* Clone the upstream `HKUDS/Vibe-Trading` project.
* Establish local branch structure and `docs_local` project management.
* Run the project locally.
* Configure `API_AUTH_KEY` safely.
* Keep shell tools disabled.
* Discover current architecture and data-source locations.
* Add a US data-source smoke test tool.
* Plan LLM provider strategy.
* Verify DeepSeek as the first main LLM provider.
* Verify one minimal native Agent research workflow.

## 2. Completed Items

### Git / Branch

* Upstream project cloned locally.
* Work isolated on `feature/bootstrap-local-setup`.
* No push performed.
* No personal fork remote configured yet.

### docs_local

Created and maintained local project-management documents, including:

* Roadmap and next tasks.
* Architecture decisions.
* Current architecture map.
* Test reports.
* Data-source discovery and smoke-test report.
* Tailscale deployment/runbook docs.
* LLM setup and provider strategy docs.
* Minimal research task doc.

### Python / Node Environment

* Installed and used Python 3.11.
* Created `.venv`.
* Installed backend dependencies.
* Installed frontend dependencies.
* Confirmed Node/npm frontend dev path works.

### Backend / Frontend / CLI

Verified:

* Backend starts on `127.0.0.1:8899`.
* Frontend starts on `127.0.0.1:5899`.
* Backend `/health` works.
* Backend `/api` works.
* Frontend HTML loads.
* CLI help and run path work.

### API_AUTH_KEY

* Created local ignored `agent/.env`.
* Generated `API_AUTH_KEY`.
* Did not commit `agent/.env`.
* Did not print the full key.

### Tailscale / Remote Access

* Produced Tailscale deployment plan and runbook.
* User decided to defer Tailscale CLI dry run.
* Remote control is temporarily handled through remote desktop tooling.
* Web UI remote exposure is not a Phase 0 target.

### US Data Source Smoke Test

* Added `scripts/smoke_test_us_data_sources.py`.
* Added `local_reports/` ignore rule.
* Ran quick smoke test.
* Confirmed Yahoo direct, Sina, and Eastmoney worked for quick AAPL/MSFT daily checks.
* Confirmed yfinance remains degraded in this environment.

### LLM Provider

* Documented supported provider metadata from code.
* Created investment-research LLM provider strategy.
* Configured DeepSeek locally in ignored `agent/.env`.
* Verified DeepSeek with provider doctor, hello test, and JSON-output prompt.

### Minimal Research Task

* Ran one minimal SPY research task through the native Vibe-Trading Agent workflow.
* The task completed successfully.
* The answer was generated in Chinese and included a no-investment-advice disclaimer.

### Web UI Product Smoke Test

* Started backend and frontend on localhost.
* Verified Home, Settings, Agent, Runtime, and session-history surfaces.
* Ran `SPY.US` through the Web UI and generated a visible report.
* Ran `600519.SH` through the Web UI and generated a visible A-share report.
* Confirmed shell tools remained disabled.

## 3. Unfinished Items

* Tailscale dry run: deferred.
* yfinance TLS issue: not fixed.
* Full US data-source smoke test: not yet run.
* `a-stock-data`: not integrated.
* LLM router: not implemented.
* Symbol normalization: not designed yet.
* Custom provider plugin framework: not designed yet.

## 4. Key Verification Results

Backend command:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

DeepSeek provider:

* Provider: `deepseek`.
* Model: `deepseek-v4-pro`.
* Base URL: `https://api.deepseek.com/v1`.
* Adapter mode: `auto`, using OpenAI-compatible fallback because `langchain-deepseek` is not installed.
* Verification: provider doctor, hello prompt, and JSON prompt succeeded.

Minimal research task:

```bash
.venv/bin/vibe-trading run -p "请生成 SPY 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。"
```

Run result:

* Status: success.
* Run ID: `20260705_162441_99_2b6f81`.
* Run directory: `agent/runs/20260705_162441_99_2b6f81`.
* Data tools called: `get_market_data`, `get_stock_profile`, `get_stock_news`.
* Report generated: yes.
* Advice boundary: output stated it was not investment advice.

Web UI product smoke test:

* Backend: `127.0.0.1:8899`.
* Frontend: `127.0.0.1:5899`.
* SPY.US session: `884ecc8115d1`.
* SPY.US run ID: `20260705_164326_08_79a439`.
* 600519.SH session: `bd1bbb81c6fc`.
* 600519.SH run ID: `20260705_164700_99_303723`.
* Both reports were visible in the Agent page session history.
* Runtime page loaded in read-only mode; broker connectors were not authorized or started.

## 5. Issues Exposed

* Bare symbols such as `SPY` can cause partial tool-routing failures; future prompts/tests should prefer `SPY.US` or `AAPL.US`.
* Yahoo/yfinance profile/options paths showed SSL or connection-reset failures.
* yfinance TLS issue remains unresolved.
* No multi-model LLM router exists yet.
* No unified A-share symbol convention exists yet.
* No `a-stock-data` adapter exists yet.
* Reports page stayed on `Loading...` during the Web UI smoke test.
* A-share detailed run status was success, but the `/runs` list showed `unknown`; this status consistency issue needs follow-up.

## 6. Security Status

* `agent/.env` was not committed.
* Full `API_AUTH_KEY` was not printed.
* Full DeepSeek API key was not printed.
* Shell tools remain disabled with `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* No public network exposure.
* No auth logic changes.
* No provider chain changes.
* No business code changes.

## 7. Phase 0 Conclusion

Phase 0 is complete: local deployment, main LLM provider, and the native minimal research workflow have all been verified successfully. The project can now enter Phase 1 architecture-improvement planning.
