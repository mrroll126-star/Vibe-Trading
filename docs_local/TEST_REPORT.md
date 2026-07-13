# Test Report

## 2026-07-13 Fixture-first ToolExecutionResult Transport Proof

Scope:

* Offline generic tool-result transport only.
* No real Agent task, Web UI, live data, `.env` read, or runtime artifact.

Implementation verification:

* `ToolRegistry.execute(...)` remains compatible with string-returning tools.
* `ToolRegistry.execute_with_metadata(...)` returns immutable per-call
  `ToolExecutionResult` values.
* AgentLoop serial and parallel paths pass call-bound metadata explicitly to
  finalization; legacy result text alone reaches the LLM context.
* Flag off retains the legacy financial trace shape; flag on sends fixture
  metadata through the existing provenance projector.
* Corrected projector interpretation of explicit `fallback.used=false` so it
  does not falsely label a primary result as fallback.

Commands and results:

```text
.venv/bin/python -m unittest agent.tests.test_tool_execution_result_transport
8 passed

.venv/bin/python -m unittest agent.tests.test_financial_runtime_provenance agent.tests.test_financial_provenance_projection agent.tests.test_tool_dual_write agent.tests.test_tool_result_serializer agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder agent.tests.test_research_artifact_generator
49 passed

.venv/bin/python -m unittest agent.tests.test_tool_timeout
0 unittest-discovered tests; command completed successfully

.venv/bin/python -m unittest agent.tests.test_shell_tool_capability
6 passed

.venv/bin/python -m compileall -q agent/src agent/tests scripts
passed
```

Test environment limitation:

* The pytest-based AgentLoop modules could not be imported because this local
  `.venv` does not contain `pytest` (`ModuleNotFoundError`). No dependency was
  installed for this fixture-only task. The new unittest coverage exercises the
  changed serial and parallel transport functions directly.

Boundary:

* `FinancialStatementsTool` did not change and does not yet produce real
  primary/fallback execution metadata.

## 2026-07-13 A-share Financial Execution Metadata Producer

Scope:

* Fixture/mocked Eastmoney and Sina/a-stock-data execution only.
* No real Agent task, Web UI, live request, `.env` read, or production artifact.

Verified behavior:

* A-share Eastmoney primary success returns call-bound metadata with
  `provider=eastmoney`, `source=eastmoney`, `upstream=null`, and
  `fallback.used=false`.
* A successful fallback identifies `a_stock_data` as final provider and carries
  the adapter's actual `sina_financial_report` / `a-stock-data` fields.
* All-failed and fallback-ineligible paths preserve legacy JSON and never claim
  a successful provider.
* Primary errors are first-line, redacted, and bounded before metadata storage.
* The legacy `execute()` method remains string-only; `execute_with_metadata()`
  is the additive producer path used by ToolRegistry transport.

Commands and results:

```text
.venv/bin/python -m unittest agent.tests.test_financial_execution_metadata_producer
10 passed

.venv/bin/python -m unittest agent.tests.test_tool_execution_result_transport agent.tests.test_financial_runtime_provenance agent.tests.test_financial_provenance_projection agent.tests.test_financial_normalizer agent.tests.test_financial_normalizer_pipeline agent.tests.test_financial_confidence_integration agent.tests.test_tool_result_serializer agent.tests.test_tool_dual_write agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder agent.tests.test_research_artifact_generator agent.tests.test_real_trace_observation agent.tests.test_real_trace_artifact_observation
88 passed

.venv/bin/python -m unittest agent.tests.test_shell_tool_capability
6 passed

.venv/bin/python -m unittest agent.tests.test_financial_statements_tool agent.tests.test_a_stock_data_financials_fallback
36 passed

.venv/bin/python -m compileall -q agent/src agent/tests scripts
passed
```

Total executed unittest cases: 140 passed.

Pytest-based AgentLoop modules were not run because the existing virtual
environment does not include `pytest`; no dependency was installed.

Status: basic local deployment executed on 2026-07-05.

No business code was modified. No real `.env`, token, API key, or OAuth file was created.

## 1. Environment Check

Initial state:

| Check | Result |
| -- | -- |
| Repo path | `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading` |
| Branch | `feature/bootstrap-local-setup` |
| Git status before install | `?? docs_local/` |
| System `python3` | Python 3.9.6 |
| System `python` | not found |
| Existing `python3.11` / `python3.12` | not found before install |
| Homebrew | Homebrew 6.0.1 |
| Node.js | v24.16.0 |
| npm | 11.13.0 |
| pnpm | 11.7.0 |
| Docker | not found |

Python 3.11 was installed with Homebrew:

```bash
brew install python@3.11
```

Result:

* Success.
* Python installed as `/opt/homebrew/bin/python3.11`.
* Version: Python 3.11.15.
* System Python was not modified.

## 2. Virtual Environment

Commands:

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/python --version
.venv/bin/pip --version
```

Result:

* Success.
* Virtual environment path: `.venv`.
* Python: 3.11.15.
* pip: 26.1.2.
* `.venv/` is already ignored by `.gitignore`.
* Final `.venv` size: about 955 MB.

## 3. Backend Dependency Install

Commands:

```bash
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e .
```

Result:

* Success.
* Installed editable package `vibe-trading-ai==0.1.10`.
* CLI reports `vibe-trading 0.1.10`.
* No API key was needed for installation.
* No real `.env` was created.

Notes:

* Installation was large but completed with prebuilt macOS arm64 wheels for the main scientific stack.
* No dependency version changes were made.

## 4. Frontend Dependency Install

Lockfile found:

* `frontend/package-lock.json`

Command:

```bash
cd frontend
npm install
```

Result:

* Success.
* Installed 364 packages.
* npm audit found 0 vulnerabilities.
* Warning: `whatwg-encoding@3.1.1` is deprecated.
* Current Node v24.16.0 worked for install.
* Final `frontend/node_modules` size: about 271 MB.

Node note:

* Project Dockerfile uses Node 20.
* If future frontend build/dev errors appear, use Node 20 LTS via nvm.

## 5. Backend Startup

Command:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Result:

* Success.
* Backend listened on `127.0.0.1:8899`.
* Server was stopped after validation.
* No shell tools were enabled.
* No remote interface was exposed.

Startup output highlights:

* `Uvicorn running on http://127.0.0.1:8899`
* Warning: no frontend production build found at `frontend/dist`.
* Preflight: LLM provider not configured, so agent research runs cannot function yet.
* Preflight: yfinance failed with curl/OpenSSL TLS error.
* Preflight: OKX reachable, akshare installed, ccxt installed.

Important failure/warning details:

```text
LANGCHAIN_PROVIDER not set in .env (agent cannot function)
yfinance SSLError: curl: (35) TLS connect error ... OPENSSL_internal:invalid library (0)
```

Impact:

* API server can start and health works.
* Full agent research requires LLM provider configuration or Ollama.
* US/HK equity backtest through yfinance may fail until the curl/OpenSSL issue is investigated.

## 6. Frontend Startup

Command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Result:

* Success.
* Vite started on `http://127.0.0.1:5899/`.
* Web UI HTML was reachable by curl.
* Frontend was stopped after validation.

## 7. Minimal Validation

Commands:

```bash
curl -fsS --max-time 5 http://127.0.0.1:8899/health
curl -fsS --max-time 5 http://127.0.0.1:8899/api
.venv/bin/vibe-trading --help
curl -fsS --max-time 5 http://127.0.0.1:5899/
curl -fsS --max-time 5 http://127.0.0.1:8899/runs
curl -fsS --max-time 5 http://127.0.0.1:5899/sessions
curl -fsS --max-time 5 http://localhost:8899/health
```

Results:

| Check | Result |
| -- | -- |
| Backend `/health` | Success, returned `healthy` |
| Backend `/api` | Success, returned service metadata |
| CLI help | Success |
| Frontend HTML | Success |
| Local protected `/runs` | Success, returned `[]` from loopback dev mode |
| Frontend proxy `/sessions` | Success, returned `[]` |
| `localhost` health | Success |

API auth observation:

* Local loopback access works without `API_AUTH_KEY`.
* Non-local access was not exposed or tested.
* Project code requires `API_AUTH_KEY` for non-local sensitive access.

## 8. Sensitive File Check

Command:

```bash
find . -maxdepth 3 \( -name '.env' -o -name '.env.*' -o -iname '*token*' -o -iname '*oauth*' -o -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' -o -iname '*.duckdb' -o -iname '*.log' \) -not -path './.git/*' -not -path './.venv/*' -not -path './frontend/node_modules/*' -print
```

Result:

* Found only `agent/.env.example` and test files whose names mention token/OAuth.
* No real `.env` was created.
* No token/API key/OAuth/cache/database/log artifact was created in tracked paths.

## 9. Services Stopped

After validation:

* Backend process was stopped with Ctrl+C.
* Frontend process was stopped with Ctrl+C.
* No process was listening on ports 8899 or 5899.

## 10. Failed Or Degraded Items

| Item | Status | Error Summary | Suggested Next Step |
| -- | -- | -- | -- |
| LLM provider | Not configured | `LANGCHAIN_PROVIDER not set` | Choose Ollama, OpenRouter, OpenAI, DeepSeek, or OAuth path; configure only in ignored local env |
| yfinance preflight | Failed | curl/OpenSSL TLS connect error | Investigate `curl_cffi`/cert/OpenSSL issue before relying on yfinance |
| Docker | Not available | `docker: command not found` | Optional: install Docker Desktop later if Docker path is desired |
| Remote access | Not tested | intentionally not exposed | Configure `API_AUTH_KEY` and CORS before Tailscale access |

## 11. Web UI Product Smoke Test

Date: 2026-07-05.

Commands:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Result:

* Backend started on `127.0.0.1:8899`.
* Frontend started on `127.0.0.1:5899`.
* Web UI Home, Settings, Agent, Runtime, and session history were checked.
* DeepSeek provider was shown as configured in Settings without exposing the key.
* Shell tools remained disabled.

Research tasks:

| Target | Prompt Channel | Run ID | Result | Notes |
| -- | -- | -- | -- | -- |
| `SPY.US` | Web UI Agent page | `20260705_164326_08_79a439` | success | Report visible in UI; trace ended success. |
| `600519.SH` | Web UI Agent page | `20260705_164700_99_303723` | success in detail endpoint and trace | Report visible in UI; `/runs` list showed `unknown`, so status-list consistency needs follow-up. |

Issues:

* `/reports` page stayed on `Loading...` during this smoke test.
* No obvious trace viewer or export/copy control was found in the quick UI pass.
* One web-reader call for the A-share task hit a remote-reader block, but the task still completed.
* Backend logs showed one A-share fund-flow connection interruption and Yahoo profile SSL failures; these did not prevent the final Web reports from being generated.
* Backend and frontend were stopped after the smoke test; ports `8899` and `5899` were clear.

See:

* `docs_local/WEB_UI_SMOKE_TEST_REPORT.md`
* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`

## 15. Full US Smoke Test And A-Share Preflight

Date: 2026-07-05.

### Full US data-source smoke test

Command:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --symbols AAPL.US,MSFT.US,NVDA.US,TSLA.US,SPY.US,QQQ.US --timeout 15 --output-dir local_reports
```

Result:

| Status | Count |
| -- | --: |
| success | 40 |
| failed | 68 |
| skipped | 90 |
| unsupported | 330 |

Daily OHLCV provider results:

| Provider | Result |
| -- | -- |
| yahoo | 18/18 daily checks succeeded. |
| sina | 18/18 daily checks succeeded. |
| eastmoney | 4/18 daily checks succeeded; unstable for this symbol set. |
| stooq | 0/18 daily checks succeeded; returned no rows. |
| yfinance | 0/18 daily checks succeeded; curl/OpenSSL/TLS issue remains. |
| akshare | 0/18 daily checks succeeded for this US symbol set. |
| tiingo/fmp/finnhub/alphavantage | skipped because keys are not configured. |
| local | skipped because local data bridge is not configured. |

Short-term US provider recommendation:

1. `yahoo`
2. `sina`
3. `eastmoney` as opportunistic fallback only
4. key-gated providers after real keys are configured and tested
5. avoid relying on `yfinance` until TLS is fixed

### A-share Level 1 preflight

Symbols:

* `600519.SH`
* `300750.SZ`
* `000001.SZ`
* `601318.SH`
* `510300.SH`
* `159915.SZ`

Result:

* `tencent` returned 31 daily OHLCV rows for all six symbols.
* `akshare` returned 31 daily OHLCV rows for `510300.SH` and `159915.SZ`.
* `mootdx` and `baostock` dependencies are missing.
* `tushare` token is not configured.
* `eastmoney` returned no rows or connection interruptions in this lightweight loader test.
* `local` has no config for these symbols.

### A-share Level 2 minimal research tasks

| Symbol | Command Pattern | Run ID | Result | Provider/Tool Notes |
| -- | -- | -- | -- | -- |
| `600519.SH` | `.venv/bin/vibe-trading run -p "...600519.SH..."` | `20260705_170327_44_d10190` | success | A-share tools and web search succeeded; yfinance/Tushare preflight remained degraded. |
| `300750.SZ` | `.venv/bin/vibe-trading run -p "...300750.SZ..."` | `20260705_170559_16_fc55fe` | success | Market/news/research/financial/sector/margin/shareholder tools succeeded; yfinance/Tushare preflight remained degraded. |

Security and boundary:

* No shell tools were enabled.
* No remote service was exposed.
* No provider chain was changed.
* No `a-stock-data` integration was attempted.
* `local_reports/`, `agent/runs/`, and `agent/sessions/` remain ignored and were not committed.

## 16. Symbol Normalizer Helper Tests

Date: 2026-07-05.

Implementation files:

* `agent/src/symbols/__init__.py`
* `agent/src/symbols/normalizer.py`
* `agent/tests/test_symbol_normalizer.py`

Primary test command attempted:

```bash
.venv/bin/python -m pytest agent/tests/test_symbol_normalizer.py
```

Result:

* Failed because `pytest` is not installed in the current `.venv`.
* No new dependency was installed.

Fallback test command:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer
```

Result:

* Success.
* 12 tests ran.
* Output: `OK`.

Coverage summary:

* US: `QQQ`, `SPY`, `AAPL`, `NVDA`, `QQQ.US`, invalid long ticker.
* A-share: prefix inference, explicit suffixes, exchange-prefix forms, ETF prefixes, `000001` ambiguity, `prefer_index`.
* HK: common HK codes, `.HK`, `HK.` prefix, HK context.
* Chinese names: deferred with confirmation.
* Boundary: empty input, whitespace, ambiguous short numeric, invalid mixed input.

Boundary:

* Helper is not connected to `get_market_data`.
* Helper is not connected to `get_stock_news`.
* Provider chain is unchanged.
* Existing business behavior is unchanged.

## 11. US Data Source Smoke Test

Date: 2026-07-05.

Purpose:

* Validate existing US data loaders provider-by-provider.
* Keep the test independent from core provider logic.
* Produce a repeatable local report before future data-source changes.

Files changed for this test:

* Added `scripts/smoke_test_us_data_sources.py`.
* Added `local_reports/` to `.gitignore`.
* Updated local documentation under `docs_local/`.

Commands:

```bash
.venv/bin/python -m py_compile scripts/smoke_test_us_data_sources.py
.venv/bin/python scripts/smoke_test_us_data_sources.py --quick --timeout 10 --output-dir local_reports
```

Results:

| Check | Result |
| -- | -- |
| Script syntax check | Success |
| Smoke test command | Success |
| Output JSON | Generated under ignored `local_reports/` |
| Output Markdown | Generated under ignored `local_reports/` |
| Core business code changed | No |
| Provider chain changed | No |
| Real API key required | No |

Quick run summary:

| Status | Count |
| -- | --: |
| success | 6 |
| failed | 6 |
| skipped | 10 |
| unsupported | 22 |

Successful provider checks:

* `yahoo`: AAPL/MSFT daily 1-month bars returned.
* `sina`: AAPL/MSFT daily 1-month bars returned.
* `eastmoney`: AAPL/MSFT daily 1-month bars returned.

Expected skips:

* `tiingo`: missing `TIINGO_API_KEY`.
* `fmp`: missing `FMP_API_KEY`.
* `finnhub`: missing `FINNHUB_API_KEY`.
* `alphavantage`: missing `ALPHAVANTAGE_API_KEY`.
* `local`: no local Data Bridge config at `~/.vibe-trading/data-bridge/config.yaml`.

Failures captured:

* `stooq`: returned no rows for AAPL/MSFT in this quick run.
* `akshare`: returned no rows for AAPL/MSFT in this quick run.
* `yfinance`: returned no usable rows and reproduced existing curl/OpenSSL TLS error messages.

How to rerun:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --quick --timeout 10 --output-dir local_reports
```

Fuller run, when the user approves:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --timeout 15 --output-dir local_reports
```

Important boundary:

* This test does not prove data quality or trading usefulness.
* It only checks provider availability, basic daily OHLCV shape, runtime behavior, and failure modes.

## 12. Tailscale Dry Run And API Auth Setup

Date: 2026-07-05.

Purpose:

* Prepare safe local API authentication for future Tailnet access.
* Confirm whether Tailscale is available.
* Avoid exposing services until Tailscale is installed and verified.

Commands:

```bash
pwd
git branch --show-current
git status --short
git log --oneline -5
test -f agent/.env
git check-ignore -v agent/.env
tailscale version
tailscale status
tailscale ip -4
```

Results:

| Check | Result |
| -- | -- |
| Repo path | Correct |
| Branch | `feature/bootstrap-local-setup` |
| Git status before env setup | Clean |
| `agent/.env` before setup | Missing |
| `agent/.env` ignored by Git | Yes, via `agent/.gitignore` |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS` in current shell | Not set |
| Common real LLM/API key env vars | Not found |
| Tailscale command | Not found |

Local `agent/.env` setup:

* Created ignored local file `agent/.env`.
* Generated a strong random `API_AUTH_KEY`.
* Did not print or store the full key in documentation.
* Set `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Added local frontend CORS origins for `5899`.
* Did not add any real LLM provider key.

Actual Tailnet dry run:

* Not executed.
* Reason: `tailscale` command is not installed or not available on `PATH`.
* No backend/frontend service was started on a Tailscale IP.
* No public exposure occurred.

Security result:

* `agent/.env` is ignored by Git and must remain uncommitted.
* Shell tools remain disabled.
* API auth is prepared for future remote access.
* Next remote run requires Tailscale installation/login first.

## 11. Reproduction Commands

Backend:

```bash
source .venv/bin/activate
vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Stop:

```bash
Ctrl+C
```

## 12. yfinance TLS Diagnostic

Diagnostic date: 2026-07-05.

Commands:

```bash
.venv/bin/python -c "import ssl; print(ssl.OPENSSL_VERSION)"
.venv/bin/python -c "import certifi; print(certifi.where())"
.venv/bin/python -m pip show yfinance curl_cffi requests certifi
.venv/bin/python -c "import yfinance as yf; print(yf.__version__)"
.venv/bin/python - <<'PY'
import yfinance as yf
try:
    t = yf.Ticker("AAPL")
    print(t.history(period="5d").tail())
except Exception as e:
    print(type(e).__name__)
    print(str(e)[:1000])
PY
```

Results:

| Check | Result |
| -- | -- |
| Python OpenSSL | `OpenSSL 3.6.3 9 Jun 2026` |
| certifi path | `.venv/lib/python3.11/site-packages/certifi/cacert.pem` |
| yfinance | 1.5.1 |
| curl_cffi | 0.15.0 |
| requests | 2.34.2 |
| certifi | 2026.6.17 |
| yfinance import | Success |
| `AAPL` 5d history | Failed |

Error summary:

```text
Failed to get ticker 'AAPL' reason: Failed to perform, curl: (35) Recv failure: Connection reset by peer.
SSLError
Failed to perform, curl: (35) TLS connect error: error:00000000:invalid library (0):OPENSSL_internal:invalid library (0).
```

Interpretation:

* Python and certifi are present.
* yfinance imports successfully.
* Failure occurs during yfinance network access through `curl_cffi` / libcurl TLS.
* This does not prove every US data source is broken. Direct Yahoo loader, Stooq, Eastmoney, Sina, and key-gated providers use different code paths.

Recommendation:

* Do not change provider code yet.
* Before relying on yfinance, run a focused follow-up on `curl_cffi`, certificate configuration, and macOS/Homebrew OpenSSL linkage.
* A future US provider smoke test should treat yfinance as one provider only; its failure should not fail the whole report.

## 13. DeepSeek Provider And Minimal Research Task Verification

Date: 2026-07-05.

Security boundary:

* No full DeepSeek key was printed.
* `agent/.env` remains ignored by Git.
* `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Backend and frontend were bound only to `127.0.0.1`.
* No `a-stock-data` integration.
* No provider chain changes.

DeepSeek config found:

| Item | Result |
| -- | -- |
| `LANGCHAIN_PROVIDER` | `deepseek` |
| `LANGCHAIN_MODEL_NAME` | `deepseek-v4-pro` |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` |
| `DEEPSEEK_API_KEY` | present, redacted |
| Adapter | OpenAI-compatible fallback, mode `auto` |

Commands:

```bash
.venv/bin/vibe-trading provider doctor
.venv/bin/python - <<'PY'
from src.providers.llm import build_llm
from langchain_core.messages import HumanMessage
llm = build_llm()
print(llm.invoke([HumanMessage(content='用一句话回答：你已连接成功。')]).content)
print(llm.invoke([HumanMessage(content='只输出 JSON，不要解释：{"status":"ok","task":"health_check"}')]).content)
PY
```

Provider test results:

| Test | Result |
| -- | -- |
| Provider doctor | Success |
| Hello text request | Success |
| JSON output prompt | Success |
| Auth error | None observed |
| Model-name error | None observed |
| Rate limit | None observed |

Local service commands:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Local service results:

| Check | Result |
| -- | -- |
| Backend startup | Success |
| Backend `/health` | Success |
| Backend `/api` | Success |
| Frontend startup | Success |
| Frontend HTML | Success |
| Ports after stop | 8899 and 5899 no longer listening |

Minimal research task:

```bash
.venv/bin/vibe-trading run -p "请生成 SPY 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。"
```

Result:

* Status: success.
* Run ID: `20260705_162441_99_2b6f81`.
* Run directory: `agent/runs/20260705_162441_99_2b6f81`.
* Runtime: about 1 minute 12 seconds.
* Provider/model: DeepSeek `deepseek-v4-pro`.
* Provider-reported total tokens: 169,015.
* The answer included a no-investment-advice disclaimer.

Data-source notes:

* Agent called data tools.
* Some SPY data calls failed or returned unresolved because the prompt used bare `SPY`; next test should use `SPY.US`.
* Yahoo profile/options paths showed SSL or connection-reset errors.
* yfinance TLS issue remains unresolved.

Conclusion:

* DeepSeek provider is usable.
* Original Vibe-Trading Agent workflow can complete a minimal research task.
* Data-source routing/reliability needs a follow-up test with explicit `.US` symbols.

## 17. DeepSeek Model Switch Test: v4-pro To v4-flash

Date: 2026-07-05.

Scope:

* Switch local ignored `agent/.env` model from `deepseek-v4-pro` to `deepseek-v4-flash`.
* Do not print API keys.
* Do not restart backend.
* Do not run a real research task.
* Do not modify business code.

Configuration before switch:

| Item | Result |
| -- | -- |
| `LANGCHAIN_PROVIDER` | `deepseek` |
| `LANGCHAIN_MODEL_NAME` | `deepseek-v4-pro` |
| `DEEPSEEK_API_KEY` | present, redacted |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS` | `0` |

Configuration after switch:

| Item | Result |
| -- | -- |
| `LANGCHAIN_PROVIDER` | `deepseek` |
| `LANGCHAIN_MODEL_NAME` | `deepseek-v4-flash` |
| `DEEPSEEK_API_KEY` | present, redacted |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS` | `0` |

Commands:

```bash
.venv/bin/vibe-trading provider doctor

.venv/bin/python - <<'PY'
from dotenv import load_dotenv
load_dotenv('agent/.env')
from src.providers.chat import ChatLLM
client = ChatLLM()
resp = client.chat([
    {'role': 'system', 'content': 'You are a connection test. Reply briefly.'},
    {'role': 'user', 'content': '用一句话回答：你已连接成功。'},
], timeout=60)
print((resp.content or '').strip())
PY
```

Provider doctor result:

| Check | Result |
| -- | -- |
| Provider | `deepseek` |
| Model | `deepseek-v4-flash` |
| Base URL | `https://api.deepseek.com` |
| API key | set, redacted |
| Adapter | OpenAI-compatible |
| Native `langchain-deepseek` package | not installed |
| Command status | Success |

Hello test result:

| Check | Result |
| -- | -- |
| Model read from env | `deepseek-v4-flash` |
| API key present | yes, redacted |
| Request status | Success |
| Elapsed time | about 2.5 seconds |
| Response preview | `你已连接成功。` |

Conclusion:

* Local model switching works by changing `LANGCHAIN_MODEL_NAME` in ignored `agent/.env`.
* The same configured DeepSeek API key was accepted for `deepseek-v4-flash` in this local test.
* No additional key was required.
* Actual availability still depends on the user's DeepSeek account permissions and official DeepSeek model availability.
* To switch back, set `LANGCHAIN_MODEL_NAME=deepseek-v4-pro` in `agent/.env`, then restart backend or rerun provider tests.

## 18. get_market_data Freshness Wrapper MVP

Date: 2026-07-07.

Scope:

* Add freshness metadata to `get_market_data` only.
* Do not change provider fallback order.
* Do not add data sources.
* Do not fix yfinance.
* Do not change Web UI.
* Do not run a full research task.

Implemented files:

| File | Purpose |
| -- | -- |
| `agent/src/data_quality/__init__.py` | Exposes data-quality helper API. |
| `agent/src/data_quality/freshness.py` | Computes serializable freshness metadata from existing tool payloads. |
| `agent/src/market_data.py` | Adds reserved top-level `_data_quality` metadata to `get_market_data` output. |
| `agent/tests/test_data_freshness.py` | Unit tests for freshness rules and wrapper shape. |

Freshness fields added per symbol:

* `tool_name`
* `raw_input`
* `normalized_symbol`
* `market`
* `asset_type`
* `provider`
* `requested_at`
* `latest_data_date`
* `latest_data_timestamp`
* `freshness_status`
* `is_intraday_like`
* `is_official_close`
* `row_count`
* `source_success`
* `source_error`
* `warnings`

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness

.venv/bin/python -m compileall -q agent/src/data_quality agent/src/market_data.py agent/tests/test_data_freshness.py

.venv/bin/python - <<'PY'
import json
import pandas as pd
from src.market_data import fetch_market_data_json

class Loader:
    def fetch(self, codes, start_date, end_date, interval='1D'):
        df = pd.DataFrame({'close': [10.0]}, index=pd.to_datetime(['2026-07-07']))
        df.index.name = 'trade_date'
        return {codes[0]: df}

parsed = json.loads(fetch_market_data_json(
    codes=['600519.SH'],
    start_date='2026-07-07',
    end_date='2026-07-07',
    source='tencent',
    loader_resolver=lambda source: Loader,
))
assert isinstance(parsed['600519.SH'], list)
assert parsed['600519.SH'][0]['close'] == 10.0
assert parsed['_data_quality']['600519.SH']['freshness_status'] == 'fresh'
print('direct validation ok')
PY
```

Results:

| Check | Result |
| -- | -- |
| Freshness unittest | Passed, 8 tests. |
| Compile check | Passed. |
| Direct `fetch_market_data_json` validation | Passed. |
| Original per-symbol data shape preserved | Yes. |
| `_data_quality` added | Yes. |
| Daily current-date close warning | Present. |

Unable to run:

```bash
.venv/bin/python -m pytest agent/tests/test_market_data.py agent/tests/test_market_data_tool.py agent/tests/test_get_market_data_unresolved.py agent/tests/test_get_market_data_size.py
```

Result:

* Failed before test collection because the current virtual environment does not have `pytest` installed.
* Error summary: `No module named pytest`.
* No dependency changes were made just to run this command.

Conclusion:

* `get_market_data` now returns additive freshness metadata under `_data_quality`.
* Original symbol payloads are not wrapped or deleted.
* This is a metadata MVP, not a full report gate.
* Next step should make Agent reports surface `_data_quality` in Data Facts / Source Failures / Missing Data sections.

## 19. Source Summary In Reports MVP

Date: 2026-07-07.

Scope:

* Surface `get_market_data` `_data_quality` in final reports.
* Add mechanical report sections: `Data Source Summary`, `Missing Data`, and `Source Warnings`.
* Add system prompt instructions for data truthfulness.
* Do not implement a hard time-sensitive report gate.
* Do not extend freshness metadata to `fund_flow`, `news`, `research_reports`, or other tools yet.
* Do not modify provider chain, loaders, yfinance, Web UI, or data sources.

Implemented files:

| File | Purpose |
| -- | -- |
| `agent/src/data_quality/report_summary.py` | Formats `_data_quality` into report appendix sections. |
| `agent/src/data_quality/__init__.py` | Exposes report-summary helpers. |
| `agent/src/agent/loop.py` | Captures `get_market_data` `_data_quality` and appends the audit section to final content. |
| `agent/src/agent/context.py` | Adds data truthfulness instructions to the system prompt. |
| `agent/tests/test_report_data_source_summary.py` | Unit tests for summary formatting behavior. |

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness

.venv/bin/python -m unittest agent.tests.test_report_data_source_summary

.venv/bin/python -m compileall -q agent/src agent/tests

.venv/bin/python - <<'PY'
from src.data_quality import append_data_source_summary

report = '## 原始分析\n这是模型正文。'
quality = {
    '600519.SH': {
        'tool_name': 'get_market_data',
        'normalized_symbol': '600519.SH',
        'freshness_status': 'stale',
        'latest_data_date': '2026-07-06',
        'latest_data_timestamp': '2026-07-06T00:00:00',
        'requested_at': '2026-07-07T11:10:00+08:00',
        'row_count': 10,
        'source_success': True,
        'source_error': None,
        'warnings': ['Latest data date 2026-07-06 is older than requested date 2026-07-07.'],
    },
}
out = append_data_source_summary(report, quality)
assert out.startswith(report)
assert '## Data Source Summary' in out
assert 'stale' in out
assert '## Missing Data' in out
print('source summary validation ok')
PY
```

Results:

| Check | Result |
| -- | -- |
| Freshness unittest | Passed, 8 tests. |
| Report summary unittest | Passed, 8 tests. |
| Compile check | Passed. |
| Mock source-summary validation | Passed. |
| Full research task | Not run, by design to avoid unnecessary token use. |

Conclusion:

* Final Agent content now mechanically appends a data-quality audit section when `get_market_data` returns `_data_quality`.
* The implementation does not rely only on the LLM choosing to disclose source quality.
* This MVP still does not block unsafe answers; the next step is a time-sensitive report gate.

## 20. Time-sensitive Report Gate MVP

Date: 2026-07-07.

Scope:

* Block normal factual market reports when a time-sensitive prompt meets stale, missing, or unknown `get_market_data` freshness.
* Replace unsafe final content with a deterministic `Data Insufficient Report`.
* Keep Source Summary visible in blocked reports.
* Use only existing `get_market_data` `_data_quality`.
* Do not extend to `fund_flow`, `news`, `research_reports`, or other tools yet.
* Do not modify provider chain, loaders, yfinance, Web UI, or data sources.

Implemented files:

| File | Purpose |
| -- | -- |
| `agent/src/data_quality/report_gate.py` | Detects time-sensitive prompts, evaluates market-data freshness, and formats Data Insufficient Reports. |
| `agent/src/data_quality/__init__.py` | Exposes report-gate helpers. |
| `agent/src/agent/loop.py` | Applies the gate before final report content is persisted. |
| `agent/tests/test_report_gate.py` | Unit tests for gate behavior and Data Insufficient Report formatting. |

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate

.venv/bin/python -m compileall -q agent/src agent/tests

.venv/bin/python - <<'PY'
from src.data_quality import append_data_source_summary, evaluate_market_data_report_gate, format_data_insufficient_report

warning = 'Daily bar close on the current trading date may represent intraday last price, not official close.'

def meta(symbol, status, **kw):
    base = {
        'tool_name': 'get_market_data',
        'normalized_symbol': symbol,
        'freshness_status': status,
        'latest_data_date': '2026-07-07',
        'latest_data_timestamp': '2026-07-07T00:00:00',
        'requested_at': '2026-07-07T11:10:00+08:00',
        'row_count': 1,
        'source_success': True,
        'source_error': None,
        'warnings': [],
    }
    base.update(kw)
    return base

stale_quality = {'600519.SH': meta('600519.SH', 'stale', latest_data_date='2026-07-06')}
stale_gate = evaluate_market_data_report_gate('请分析 600519.SH 今天盘中表现，包括涨跌幅和成交额', stale_quality)
assert stale_gate['blocked'] is True
assert format_data_insufficient_report(stale_gate, stale_quality).startswith('# Data Insufficient Report')

fresh_quality = {'600519.SH': meta('600519.SH', 'fresh')}
fresh_gate = evaluate_market_data_report_gate('请做 600519.SH 的长期历史概览', fresh_quality)
fresh_report = append_data_source_summary('## 历史概览\n仅做历史说明。', fresh_quality)
assert fresh_gate['blocked'] is False
assert fresh_report.startswith('## 历史概览') and '## Data Source Summary' in fresh_report

close_quality = {'600519.SH': meta('600519.SH', 'fresh', warnings=[warning])}
close_gate = evaluate_market_data_report_gate('请告诉我 600519.SH 今天收盘价', close_quality)
assert close_gate['blocked'] is True
print('report gate validation ok')
PY
```

Results:

| Check | Result |
| -- | -- |
| Freshness unittest | Passed, 8 tests. |
| Report summary unittest | Passed, 8 tests. |
| Report gate unittest | Passed, 13 tests. |
| Total unittest count | 29 tests passed. |
| Compile check | Passed. |
| Mock report-gate validation | Passed. |
| Full research task | Not run, by design to avoid unnecessary token use. |

Conclusion:

* Time-sensitive market-data reports are now blocked when `get_market_data` freshness is stale, missing, or unknown.
* Blocked reports use a deterministic `Data Insufficient Report` and retain source summary details.
* This MVP still covers only `get_market_data`; other factual tools need freshness metadata before they can be gated.

## 21. Extend Data Quality Contract + No Estimate Guard MVP

Date: 2026-07-07.

Scope:

* Extend `_data_quality` MVP to `get_fund_flow`, `get_stock_news`, and `get_research_reports`.
* Keep each tool's original return envelope unchanged and only append top-level `_data_quality`.
* Extend final report Source Summary to display multiple tools by group.
* Add a rule-based No Estimate Guard for prompts that explicitly say not to estimate, guess, infer, or fabricate market facts.
* Do not modify provider chains, loaders, Web UI, yfinance, or `a-stock-data`.

Implementation summary:

| Area | Result |
| -- | -- |
| `get_fund_flow` | Adds per-symbol metadata. Inner per-symbol `error` or empty rows become `missing`. Rows with timestamp/date are assessed as fresh/stale/unknown. |
| `get_stock_news` | Adds metadata for articles/matches. Empty results become `missing`; old article dates beyond 3 calendar days become `stale` with warning; no date becomes `unknown`. |
| `get_research_reports` | Adds metadata for report rows. `ok=false`, HTTP errors, or empty reports become `missing`; old reports warn but are not blocked by this MVP. |
| Source Summary | Now groups captured `_data_quality` by `tool_name` and shows Missing Data / Source Warnings across tools. |
| No Estimate Guard | Detects explicit no-estimate prompts, strengthens the system prompt, and appends `No Estimate Warning` when estimated market-fact numbers appear. It does not rewrite the body in MVP. |

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard

.venv/bin/python -m compileall -q agent/src agent/tests

.venv/bin/python - <<'PY'
from datetime import datetime
from src.data_quality import assess_fund_flow_quality, assess_stock_news_quality, append_no_estimate_warning, format_data_source_summary
req = datetime(2026,7,7,11,10)
quality = {
  'get_fund_flow:600519.SH': assess_fund_flow_quality({'error':'Connection aborted'}, raw_input='600519.SH', symbol='600519.SH', provider='eastmoney', requested_at=req).to_dict(),
  'get_stock_news:600519.SH': assess_stock_news_quality({'ok': True, 'data': {'articles': [{'published':'2026-07-01'}]}}, raw_input='600519.SH', symbol='600519.SH', provider='eastmoney', requested_at=req).to_dict(),
}
summary = format_data_source_summary(quality)
print('fund_flow_missing=', 'Connection aborted' in summary and '### get_fund_flow' in summary)
print('stale_news_warning=', 'News may be outdated' in summary and '### get_stock_news' in summary)
warned = append_no_estimate_warning('成交额估算约 32.7 亿元。', '请分析 600519.SH，不要估算')
print('no_estimate_warning=', '## No Estimate Warning' in warned)
plain = append_no_estimate_warning('可能受行业情绪影响。', '请分析 600519.SH，不要估算')
print('plain_maybe_no_warning=', '## No Estimate Warning' not in plain)
PY
```

Results:

| Check | Result |
| -- | -- |
| Freshness unittest | Passed. |
| Report summary unittest | Passed. |
| Report gate unittest | Passed. |
| Extended data quality unittest | Passed. |
| No Estimate Guard unittest | Passed. |
| Total unittest count | 46 tests passed. |
| Compile check | Passed. |
| Mock fund-flow error validation | Passed. |
| Mock stale-news validation | Passed. |
| Mock no-estimate validation | Passed. |
| Full Web UI research task | Not run in this implementation round by design. |

Known limitations:

* No Estimate Guard only appends a warning; it does not rewrite or delete estimated sentences in MVP.
* The hard report gate still uses `get_market_data` only.
* Other A-share tools such as northbound flow, margin trading, shareholder count, sector info, and financial statements do not yet have this expanded contract.

## 22. Web UI Red-Light Prompt Retest

Date: 2026-07-07.

Purpose:

* Verify that the extended data-quality and No Estimate Guard MVPs reach the real Web UI final report path.
* Use the same A-share red-light prompt that previously exposed estimated market facts.

Prompt:

```text
请分析 600519.SH 今天盘中表现，包括最新价、涨跌幅、成交额和主要风险。只使用你实际获取到的数据；如果没有拿到当天数据，请明确说没有拿到，不要估算。
```

Result:

| Check | Result |
| -- | -- |
| Web session | `57a481605851` |
| Run ID | `20260707_173205_10_7f61dd` |
| Status | success |
| Data Insufficient Report | No |
| Reason not blocked | `get_market_data` returned fresh current-day data. |
| Data Source Summary | Present |
| Source Warnings | Present |
| Missing Data | Present |
| No Estimate Warning | Present |

Data quality observed:

| Tool | freshness_status | latest_data_date | Notes |
| -- | -- | -- | -- |
| `get_market_data` | fresh | 2026-07-07 | Current-day daily close warning: not official close. |
| `get_fund_flow` | fresh | 2026-07-07 | Fund-flow rows were disclosed in Source Summary. |
| `get_stock_news` | stale | 2026-06-29 | Stale-news warning disclosed. |
| `get_research_reports` | not called | n/a | Not shown, as expected. |

Trace-observed tools:

* `get_market_data`
* `get_fund_flow`
* `get_stock_news`
* `get_margin_trading`
* `get_sector_info`

Important finding:

* The report body still contained estimated or approximate market-fact phrasing.
* `No Estimate Warning` correctly appeared at the end of the report and listed the detected estimated market-fact statements.
* This confirms the MVP is active in Web UI, but also confirms warning-only mode does not prevent estimated text from appearing in the main body.

Conclusion:

* Web UI integration passed for Source Summary, multi-tool `_data_quality`, and No Estimate Warning.
* If the product requirement becomes “estimated market facts must never appear in the body,” the next task should be a stricter no-estimate rewrite/block gate.

## 23. Symbol Normalizer Feature-Flagged `get_market_data` Integration

Date: 2026-07-07.

Scope:

* Integrate the existing Symbol Normalizer helper only into `get_market_data`.
* Add `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`.
* Keep the flag disabled by default.
* Do not integrate `stock_news`, `fund_flow`, `research_reports`, Web UI, provider chains, loaders, yfinance, or `a-stock-data`.

Behavior:

| Case | Result |
| -- | -- |
| Flag off | Existing behavior is preserved. Bare `600519` stays `600519`; bare `QQQ` stays `QQQ`; no `_symbol_normalization` metadata is added. |
| Flag on, A-share | `600519 -> 600519.SH`, `300750 -> 300750.SZ`, `510300 -> 510300.SH`, `159915 -> 159915.SZ`. |
| Flag on, US | `QQQ -> QQQ.US`, `SPY -> SPY.US`. |
| Flag on, HK | `00700 -> 00700.HK`, `9988 -> 09988.HK`. |
| Bare `000001` | Returns `000001.SZ` candidate plus ambiguous warning, but does not force a provider call. |
| Chinese name | Requires confirmation and does not call provider. |
| Invalid symbol | Returns warning/error metadata and does not call provider. |
| Explicit symbol | `600519.SH`, `300750.SZ`, `SPY.US`, `00700.HK` remain usable. |

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization

.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard

.venv/bin/python -m compileall -q agent/src agent/tests
```

Results:

| Check | Result |
| -- | -- |
| Symbol normalizer tests | Passed, 23 tests. |
| Anti-hallucination regression tests | Passed, 46 tests. |
| Compile check | Passed. |
| Direct flag-off validation | Passed. |
| Direct flag-on `600519` validation | Passed. |
| Direct flag-on `QQQ` validation | Passed. |
| Direct Chinese-name confirmation validation | Passed. |

Known limitations:

* This is not enabled by default.
* Web UI was not retested with bare symbols in this round.
* Other tools still expect explicit symbols unless the LLM normalizes them itself.

## 24. Web UI Bare Symbol Retest

Date: 2026-07-07.

Purpose:

* Test the real Web UI path with `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1`.
* Confirm whether bare inputs reach `get_market_data`.
* Confirm whether `_data_quality` survives alongside `_symbol_normalization`.

Commands:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899

cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Result:

| Test | Run ID | Status | get_market_data argument | normalized_symbol | freshness_status | Notes |
| -- | -- | -- | -- | -- | -- | -- |
| `600519` | `20260707_175004_29_e1ff41` | completed | `600519.SH` | `600519.SH` | fresh | LLM converted input before tool call. |
| `QQQ` | `20260707_175103_82_517a2b` | completed | `QQQ.US` | `QQQ.US` | stale | Search/LLM converted input before tool call; market data latest date was 2026-07-06. |
| `00700` | `20260707_175432_05_eb20f8` | completed | `00700.HK` | `00700.HK` | fresh | LLM converted input before tool call. |
| `000001` | `20260707_175623_17_caf048` | completed | `000001.SZ` | `000001.SZ` | fresh | Ambiguous warning existed in metadata, but provider was still called. |
| `贵州茅台` | `20260707_175745_30_b963eb` | completed | `600519.SH` | `600519.SH` | fresh | Chinese name was mapped by the Agent before the normalizer could require confirmation. |

Validation:

* `_symbol_normalization` appeared in `get_market_data` results.
* `_data_quality` appeared in `get_market_data` results.
* `Data Source Summary` appeared in final reports.
* Services were local only.
* Shell tools stayed disabled.

Important limitation:

The Web UI Agent chain can rewrite the user's raw symbol before the tool-entry normalizer sees it. This means the current feature-flagged integration is compatible and useful, but it is not sufficient to enforce confirmation for ambiguous or Chinese-name inputs in real Web UI use.

## 25. Pre-tool Symbol Intent Guard Design Investigation

Date: 2026-07-08.

Scope:

* Read-only code-path investigation.
* No business code changes.
* No provider-chain changes.
* No service startup.
* No Web UI retest.

Findings:

| Question | Result |
| -- | -- |
| Original user prompt before tool execution | Available in `AgentLoop.run(user_message=...)`; also persisted to run request and trace. |
| Tool name and args before execution | Available in `AgentLoop._process_tool_calls(...)` through `tc.name` and `tc.arguments`. |
| Unified tool execution path | `_execute_single` and `_execute_parallel` both call `_invoke_tool`, which calls `ToolRegistry.execute`. |
| Best low-risk guard point | `AgentLoop` before provider execution, starting only with `get_market_data`. |
| `search_symbol` risk | It can precede `get_market_data`, and its result can lead the LLM to call a normalized ticker. |
| Current normalizer limitation | It sees only final tool args, so it cannot know whether `000001.SZ` came from explicit user intent or LLM pre-normalization of ambiguous `000001`. |

Design output:

* Added `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`.

## 26. Pure Pre-tool Symbol Intent Guard Function

Date: 2026-07-08.

Scope:

* Implement pure guard function.
* Add unittest coverage.
* Do not connect it to AgentLoop.
* Do not change tool execution or provider chains.

Files:

* `agent/src/symbols/intent_guard.py`
* `agent/tests/test_symbol_intent_guard.py`

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard

.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard

.venv/bin/python -m compileall -q agent/src agent/tests
```

Results:

| Check | Result |
| -- | -- |
| Symbol normalizer + market-data normalization + intent guard tests | Passed, 43 tests. |
| Anti-hallucination regression tests | Passed, 46 tests. |
| Compile check | Passed. |

Lightweight validation:

| Prompt / Tool | Result |
| -- | -- |
| `000001` -> `get_market_data(000001.SZ)` | `clarify`, `ambiguous_000001_requires_confirmation` |
| `贵州茅台` -> `get_market_data(600519.SH)` | `clarify`, `chinese_name_requires_confirmation` |
| `600519` -> `get_market_data(600519.SH)` | `allow`, `safe_bare_symbol_mapping` |
| `600519.SH` -> `get_market_data(300750.SZ)` | `block`, `tool_symbol_mismatch` |
| non-`get_market_data` tool | `allow`, `unsupported_tool_for_mvp` |

Boundary:

* No AgentLoop integration.
* No Web UI behavior change.
* No provider-chain change.
* No `a-stock-data` integration.

## 27. Feature-flagged AgentLoop Pre-tool Symbol Guard

Date: 2026-07-08.

Scope:

* Integrate pure guard into AgentLoop.
* Guard only `get_market_data`.
* Keep feature flag off by default.
* Do not modify provider chains, loaders, Web UI, or `a-stock-data`.

Feature flag:

```text
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_intent_guard_integration

.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard

.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard

.venv/bin/python -m compileall -q agent/src agent/tests
```

Results:

| Check | Result |
| -- | -- |
| AgentLoop guard integration tests | Passed, 10 tests. |
| Symbol-related tests | Passed, 43 tests. |
| Anti-hallucination regression tests | Passed, 46 tests. |
| Compile check | Passed. |

Lightweight validation:

| Case | Decision | Provider called |
| -- | -- | -- |
| flag on + `000001 -> 000001.SZ` | clarify | no |
| flag on + `贵州茅台 -> 600519.SH` | clarify | no |
| flag on + `600519 -> 600519.SH` | allow | yes |
| flag off + `000001 -> 000001.SZ` | allow existing path | yes |

Web UI retest:

* Completed in the next round and recorded below.

## 28. Web UI Pre-tool Symbol Guard Retest

Date: 2026-07-08.

Goal:

* Verify that `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1` and `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1` work in the real Web UI path.
* Confirm safe bare symbols still run.
* Confirm ambiguous `000001` and Chinese-name `贵州茅台` do not silently proceed as normal market-data calls.

Commands:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Web UI URL:

```text
http://127.0.0.1:5899/agent
```

Prompts tested:

| Case | Prompt | Session | Run ID | Result |
| -- | -- | -- | -- | -- |
| `600519` | `请分析 600519 今天的行情表现。只使用实际获取到的数据，不要估算。` | `66a8cff0a5b7` | `20260708_100611_10_dc3c41` | `get_market_data` allowed as `600519.SH`; final report was blocked by stale current-day data. |
| `QQQ` | `请分析 QQQ 最近行情表现。只使用实际获取到的数据，不要估算。` | `541e9b698014` | `20260708_100748_61_145e43` | `get_market_data` allowed as `QQQ.US`; report completed. |
| `00700` | `请分析 00700 最近行情表现。只使用实际获取到的数据，不要估算。` | `4f38726ed856` | `20260708_100758_62_0f00eb` | `get_market_data` allowed as `00700.HK`; report completed. |
| `000001` | `请分析 000001 今天的行情表现。只使用实际获取到的数据，不要估算。` | `634e6290c0ab` | `20260708_100809_64_c7f4c7` | `get_market_data` blocked by pre-tool guard; final answer asked for `000001.SZ` vs `000001.SH`. |
| `贵州茅台` | `请分析 贵州茅台 今天的行情表现。只使用实际获取到的数据，不要估算。` | `036be2933e75` | `20260708_100820_64_0082d9` | `get_market_data` blocked by pre-tool guard; final answer asked to confirm `600519.SH`. |
| `600519.SH` | `请分析 600519.SH 今天的行情表现。只使用实际获取到的数据，不要估算。` | `ce1ed7471c1c` | `20260708_100832_19_f3a59b` | Explicit symbol allowed; final report was blocked by stale current-day data. |

Trace findings:

| Case | `get_market_data` guard result | `_data_quality` | Important note |
| -- | -- | -- | -- |
| `600519` | allowed | present; `stale`, latest `2026-07-07`, provider `tencent` | Time-sensitive gate correctly produced `Data Insufficient Report`. |
| `QQQ` | allowed | present; `stale`, latest `2026-07-07`, provider `yahoo` | Yahoo profile SSL failure still appeared for `get_stock_profile`. |
| `00700` | allowed | present; `fresh`, latest `2026-07-08`, provider `yahoo` | Daily close warning appeared; research-report path was unsupported for HK. |
| `000001` | blocked / clarify | no market-data `_data_quality` because provider was not called | Other tools still ran with `000001.SZ`. |
| `贵州茅台` | blocked / clarify | no market-data `_data_quality` because provider was not called | Other tools still ran with `600519.SH`. |
| `600519.SH` | allowed | present; `stale`, latest `2026-07-07`, provider `tencent` | No false block on explicit symbol. |

Pass criteria:

* Feature flags were honored in the Web UI path: passed.
* Safe bare symbols were allowed: passed.
* Explicit symbol was allowed: passed.
* `get_market_data` was blocked for ambiguous/name-based intent: passed.
* No provider tool should run for ambiguous/name-based intent before confirmation: not fully passed.

Overall result:

* Partial pass.
* The current MVP should not be default-enabled yet.
* Next step should extend symbol intent protection to all stock-specific provider tools, not only `get_market_data`.

Shutdown:

* Backend and frontend were stopped.
* `lsof -i :8899` returned no listener.
* `lsof -i :5899` returned no listener.

## 29. Extended Pre-tool Symbol Guard To Stock-specific Tools

Date: 2026-07-08.

Goal:

* Extend `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD` from `get_market_data` to the first batch of stock-specific tools.
* Keep the flag off by default.
* Preserve flag-off behavior.
* Do not call providers when the guard returns `clarify` or `block`.

Covered tools:

* `get_market_data`
* `get_fund_flow`
* `get_stock_news`
* `get_research_reports`
* `get_sector_info`

Not covered:

* `web_search`
* `read_url`
* `search_symbol`
* `read_document`

Read-only tool-parameter findings:

| Tool | Symbol field | Notes |
| -- | -- | -- |
| `get_market_data` | `codes` | Multi-symbol list. |
| `get_fund_flow` | `codes` | Multi-symbol list. |
| `get_stock_news` | `code` | Single stock when `scope=stock`; broad market when `scope=global`. |
| `get_research_reports` | `code` | A-share single-symbol reports. |
| `get_sector_info` | `code` | Single-symbol membership mode; ranking mode is broad-market. |

Validation commands:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

```text
Ran 45 tests in 0.072s
OK
```

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

```text
Ran 68 tests in 0.067s
OK
```

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

```text
Ran 46 tests in 0.003s
OK
```

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result: passed.

Lightweight mock validation:

| Case | Result |
| -- | -- |
| flag on + `get_fund_flow` + prompt `000001` + tool symbol `000001.SZ` | `clarify`; `_invoke_tool` calls = 0. |
| flag on + `get_stock_news` + prompt `贵州茅台` + tool symbol `600519.SH` | `clarify`; `_invoke_tool` calls = 0. |
| flag on + `get_sector_info` + prompt `600519` + tool symbol `600519.SH` | allowed; `_invoke_tool` calls = 1. |
| flag on + `web_search` | allowed; `_invoke_tool` calls = 1. |
| flag off + `get_fund_flow` + prompt `000001` + tool symbol `000001.SZ` | existing behavior; `_invoke_tool` calls = 1. |

Status:

* Passed local unittest and mock validation.
* Web UI retest was not run in this round.
* Feature flags should remain off by default until Web UI retest passes.

## 30. Web UI Stock-specific Symbol Guard Retest

Date: 2026-07-08.

Goal:

* Verify the extended stock-specific symbol guard in the real Web UI path.
* Confirm `000001` and `贵州茅台` do not reach first-batch stock providers before clarification.
* Confirm safe `600519` and explicit `600519.SH` still work.

Commands:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Prompts:

| Case | Session | Run ID | Result |
| -- | -- | -- | -- |
| `000001` | `1a31b77c4894` | `20260708_103045_64_c24182` | Passed. Guard clarified all requested stock-specific tools. |
| `贵州茅台` | `ba42f63b650e` | `20260708_103113_12_894f58` | Passed. Guard clarified all requested stock-specific tools. |
| `600519` | `2927b3cd72ba` | `20260708_103129_14_e84c02` | Passed. Allowed as `600519.SH`; report gate blocked stale same-day market facts. |
| `600519.SH` | `211a82a9a415` | `20260708_103153_15_bc8245` | Passed. Explicit symbol allowed; report gate blocked stale same-day market facts. |

Guard evidence from local session traces:

| Case | `get_market_data` | `get_fund_flow` | `get_stock_news` | `get_sector_info` |
| -- | -- | -- | -- | -- |
| `000001` | clarified, no provider | clarified, no provider | clarified, no provider | clarified, no provider |
| `贵州茅台` | clarified, no provider | clarified, no provider | clarified, no provider | clarified, no provider |
| `600519` | allowed, provider called | allowed, provider called | allowed, provider called | allowed, provider called |
| `600519.SH` | allowed, provider called | allowed, provider called | allowed, provider called | allowed, provider called |

Observed data quality on allowed runs:

| Case | Tool | Freshness | Latest date | Provider |
| -- | -- | -- | -- | -- |
| `600519` | `get_market_data` | `stale` | 2026-07-07 | tencent |
| `600519` | `get_fund_flow` | `missing` | n/a | eastmoney |
| `600519` | `get_stock_news` | `fresh` | 2026-07-07 | eastmoney |
| `600519.SH` | `get_market_data` | `stale` | 2026-07-07 | tencent |
| `600519.SH` | `get_fund_flow` | `missing` | n/a | eastmoney |
| `600519.SH` | `get_stock_news` | `fresh` | 2026-07-07 | eastmoney |

Shutdown:

* Backend and frontend were stopped.
* `lsof -i :8899` returned no listener.
* `lsof -i :5899` returned no listener.

Result:

* Web UI stock-specific symbol guard retest passed.
* Feature flags should still remain off by default until one more boundary retest covers `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.
## 2026-07-08 Web UI Boundary Retest For Stock-specific Symbol Guard

Purpose:

Verify the stock-specific symbol guard in the real Web UI path after extending it beyond `get_market_data`.

Feature flags used for this local test only:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Backend command:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend command:

```bash
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Service boundary:

* Backend: `127.0.0.1:8899`.
* Frontend: `127.0.0.1:5899`.
* Public exposure: no.
* Shell tools: disabled.
* Services stopped after test.

Results:

| Prompt input | Session ID | Run ID | Result | Key evidence |
| -- | -- | -- | -- | -- |
| `QQQ` | `56e5272ab623` | `20260708_104158_24_8d4f78` | Pass | Allowed, normalized to `QQQ.US`, no clarification, `Data Source Summary` present. |
| `00700` | `dd90f724f8df` | `20260708_104211_92_abb605` | Pass | Allowed, normalized to `00700.HK`, no clarification, `Data Source Summary` present. |
| `000001.SZ` | `aacc86b161c4` | `20260708_104224_94_85bca8` | Pass | Explicit stock allowed; stale current-day data triggered `Data Insufficient Report`. |
| `000001.SH` | `811ea87008ce` | `20260708_104237_60_8d8e5a` | Pass with backlog | Explicit index market data allowed; `get_sector_info` was blocked when called without auditable symbol, indicating asset-type-aware routing work is needed. |

Known issues observed:

* Yahoo/yfinance profile path still has TLS failures.
* Some web search / read URL calls timed out or returned HTTP 403.
* `000001.SH` index prompt can trigger stock-specific or market-wide tools that are not asset-type aware enough.

Conclusion:

The stock-specific symbol guard works in the real Web UI path for `QQQ`, `00700`, `000001.SZ`, and `000001.SH`. Keep both feature flags off by default until the default-enable decision is made.

## 2026-07-08 Asset-type-aware Tool Routing Read-only Investigation

Purpose:

Design the next routing layer after symbol intent guard. This was a read-only investigation plus documentation update.

Commands / checks:

* Confirmed branch and Git status.
* Confirmed ignored sensitive/runtime paths:
  * `agent/.env`
  * `agent/runs`
  * `agent/sessions`
  * `local_reports`
* Read tool files under `agent/src/tools`.
* Read `agent/src/agent/loop.py`, `agent/src/agent/tools.py`, `agent/src/agent/context.py`.
* Read `agent/src/symbols/normalizer.py`, `agent/src/symbols/config.py`, and `agent/src/symbols/intent_guard.py`.

Investigation result:

* Current tool selection is primarily LLM-driven.
* Tool descriptions mention markets and use cases, but there is no structured `asset_type` compatibility metadata on `BaseTool`.
* Symbol Normalizer can output `asset_type`.
* AgentLoop does not currently choose or block tools based on `asset_type`.
* `000001.SH` should be allowed for market data, but stock/company-specific tools require routing policy.

No commands were run against live services. No tests were executed because this was a design-only round.

## 2026-07-08 Pure Asset-type Tool Routing Guard

Purpose:

Implement the first pure-function step for asset-type-aware tool routing without changing runtime behavior.

Files added:

* `agent/src/tools/routing_guard.py`
* `agent/tests/test_tool_routing_guard.py`

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard
```

Result:

* Passed.
* 27 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 68 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight pure-function validation:

| Case | Result |
| --- | --- |
| `get_market_data` + `000001.SH` + `index` | allow |
| `get_sector_info` + `000001.SH` + `index` | block |
| `get_financial_statements` + `510300.SH` + `etf` | block |
| `get_margin_trading` + `510300.SH` + `etf` | warn |
| `web_search` + `000001.SH` + `index` | allow |

Boundary:

* Not integrated into AgentLoop.
* Does not affect real tool calls.
* Does not modify provider chain.
* Does not modify loaders.
* Does not modify Web UI.
* Does not integrate `a-stock-data`.

## 2026-07-08 Feature-flagged Asset-type Routing Guard Integration

Purpose:

Connect pure asset-type routing guard to AgentLoop behind a default-off feature flag.

Feature flag:

```bash
VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1
```

Default:

Off. No `.env` change is required and no `.env` file was committed.

Files changed:

* `agent/src/symbols/config.py`
* `agent/src/agent/loop.py`
* `agent/tests/test_tool_routing_guard_integration.py`

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 43 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 68 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight mock validation:

| Case | Provider/tool called | Result |
| --- | ---: | --- |
| flag on + `get_sector_info` + `000001.SH` | 0 | block |
| flag on + `get_financial_statements` + `510300.SH` | 0 | block |
| flag on + `get_margin_trading` + `510300.SH` | 1 | warn |
| flag on + `get_market_data` + `000001.SH` | 1 | allow |
| flag off + `get_sector_info` + `000001.SH` | 1 | allow / no intercept |

Boundary:

* Feature flag default is off.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.
* Web UI routing retest has not been run yet.

## 2026-07-08 Fix Parallel Asset-type Routing Guard

Purpose:

Fix the Web UI path where readonly tools run in parallel and previously skipped the Asset-type Routing Guard.

Root cause:

`_execute_single` ran Symbol Intent Guard and Asset-type Routing Guard, but `_execute_parallel` only ran Symbol Intent Guard. Real Web UI research tasks commonly call multiple readonly tools in one batch, so ETF/index routing rules were bypassed.

Files changed:

* `agent/src/agent/loop.py`
* `agent/tests/test_tool_routing_guard_integration.py`

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 53 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 68 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight mock validation:

| Case | Provider/tool called | Result |
| --- | ---: | --- |
| flag on + parallel `get_financial_statements` + `510300.SH` | 0 | block |
| flag on + parallel `get_margin_trading` + `510300.SH` | 1 | warn + `_tool_routing_guard` |
| flag on + parallel `get_stock_news` + `QQQ.US` | 1 | warn + `_tool_routing_guard` |
| flag on + parallel `get_sector_info(mode=ranking)` | 1 | allow |
| flag off + parallel `get_financial_statements` + `510300.SH` | 1 | allow / no intercept |

Boundary:

* Feature flag default remains off.
* No provider-chain changes.
* No loader changes.
* No Web UI code changes.
* No `a-stock-data` integration.
* Web UI retest after the fix has not been run yet.

## 2026-07-08 Market-wide Stock News Guard Exemption

Purpose:

Fix a false positive where `get_stock_news(scope=global)` was blocked by Pre-tool Symbol Intent Guard even though it is a market-wide news request and does not require a single symbol.

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 83 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 53 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight mock validation:

| Case | Provider/tool called | Result |
| --- | ---: | --- |
| `get_stock_news(scope=global)` | 1 | allow |
| `get_stock_news(symbol=000001.SZ)`, prompt `000001` | 0 | clarify |
| `get_sector_info(mode=ranking)` | 1 | allow |
| `get_sector_info(symbol=000001.SZ)`, prompt `000001` | 0 | clarify |

Boundary:

* Feature flag default remains off.
* Symbol-specific news calls remain guarded.
* No provider-chain changes.
* No loader changes.
* No Web UI code changes.
* No `a-stock-data` integration.
* Web UI retest has not been rerun after this fix.

## 2026-07-08 Default-enable Safety Guards

Purpose:

Make the verified safety guards active by default while keeping Symbol Normalizer opt-in.

Default policy:

| Feature | Environment variable | Default | Override |
| --- | --- | --- | --- |
| Symbol Normalizer | `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` | off | `1/true/yes/on` enables |
| Pre-tool Symbol Intent Guard | `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD` | on | `0/false/no/off` disables |
| Asset-type Routing Guard | `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD` | on | `0/false/no/off` disables |

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 87 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 56 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Behavior verified:

* Default config clarifies ambiguous `000001` before stock-specific provider calls.
* Default config blocks ETF financial statements for `510300.SH`.
* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=0` disables the symbol guard.
* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=false` disables the symbol guard.
* `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=0` disables the routing guard.
* `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=false` disables the routing guard.
* `get_stock_news(scope=global)` remains allowed.
* `get_sector_info(mode=ranking)` remains allowed.
* Symbol Normalizer remains default off and only turns on with explicit enabled values.

Boundary:

* No provider-chain changes.
* No loader changes.
* No Web UI code changes.
* No `a-stock-data` integration.
* No shell tools enabled.
* No remote exposure.

## 2026-07-08 Market-wide Benchmark Routing Policy Design

Purpose:

Design how explicit market-wide prompts can use documented benchmark symbols without disabling Symbol Guard.

Read-only discovery:

* `get_stock_news(scope=global)` is already allowed by Symbol Intent Guard when no symbol is supplied.
* `get_stock_news(mode=global|market|all|sector)` and broad market-news query hints are also allowed when no symbol is supplied.
* `get_sector_info(mode=ranking|list|overview)` is allowed without a symbol.
* `get_market_data` can fetch multiple symbols in one call, but there is no benchmark policy exemption yet.
* Current reports can show Data Source Summary, Missing Data, Source Warnings, and routing metadata; they do not yet show Benchmark Selection Summary.

Documents added/updated:

* Added `docs_local/MARKET_WIDE_BENCHMARK_ROUTING_POLICY.md`.
* Updated guard design, routing design, normalizer plan, roadmap, backlog, next tasks, worklog, and changelog.

Commands executed:

```bash
pwd
git branch --show-current
git status --short
git log --oneline -5
git ls-files agent/.env agent/runs agent/sessions local_reports
```

Result:

* Branch: `feature/bootstrap-local-setup`.
* Working tree was clean before this documentation task.
* Sensitive/runtime paths are not tracked by Git.

Boundary:

* Documentation-only task.
* No tests were required because no business code changed.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.

## 2026-07-08 Pure Market-wide Benchmark Policy

Purpose:

Implement the first phase of Market-wide Benchmark Routing Policy as a pure helper with tests.

Files added:

* `agent/src/symbols/benchmark_policy.py`
* `agent/tests/test_benchmark_policy.py`

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_benchmark_policy
```

Result:

* Passed.
* 25 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 87 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 56 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight pure-function validation:

| Case | Result |
| --- | --- |
| `A股今天怎么样` + `get_market_data` | `allow_benchmark`, market `cn` |
| `美股今天怎么样` + `get_market_data` | `allow_benchmark`, market `us` |
| `港股今天怎么样` + `get_market_data` | `allow_benchmark`, market `hk` |
| `看看市场` | `ask_for_confirmation` |
| `贵州茅台今天怎么样` | `not_market_wide` |
| `A股今天怎么样` + `get_financial_statements` | `block` |
| `A股今天怎么样` + `get_market_data(symbol=600519.SH)` | `block` |
| `A股今天怎么样` + `get_market_data(symbol=000001.SH)` | `allow_benchmark` |

Boundary:

* Pure helper only.
* No AgentLoop integration.
* No real tool-call behavior changed.
* No feature flag default changed.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.

## 2026-07-08 Feature-flagged Market-wide Benchmark Policy Integration

Purpose:

Connect the pure benchmark policy to the AgentLoop pre-tool guard path behind a default-off feature flag.

Feature flag:

```bash
VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY=1
```

Default:

Off.

Commands executed:

```bash
.venv/bin/python -m unittest agent.tests.test_benchmark_policy agent.tests.test_benchmark_policy_integration
```

Result:

* Passed.
* 39 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 87 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 56 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight mock validation:

| Case | Provider called | Result |
| --- | ---: | --- |
| flag on + `A股今天怎么样` + `get_market_data(000001.SH)` | 1 | `allow_benchmark` + `_benchmark_policy` |
| flag on + `A股今天怎么样` + `get_market_data(600519.SH)` | 0 | benchmark policy `block` |
| flag on + `看看市场` + `get_market_data(000001.SH)` | 0 | benchmark policy `ask_for_confirmation` |
| flag on + `贵州茅台今天怎么样` + `get_market_data(000001.SH)` | 0 | Symbol Guard `clarify` |
| flag on + `A股今天怎么样` + `get_financial_statements(000001.SH)` | 0 | benchmark policy `block` |
| flag off + `A股今天怎么样` + `get_market_data(000001.SH)` | 0 | existing Symbol Guard `block` |

Boundary:

* Feature flag default remains off.
* Flag off preserves current Symbol Guard behavior.
* Benchmark policy does not bypass Asset-type Routing Guard.
* Benchmark policy does not bypass Data Freshness Guard.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.
* Web UI retest not run in this task.

## 2026-07-08 Benchmark Batch Handling Fix

Goal:

Fix the A-share market-wide benchmark batch issue found in the Web UI/API same-origin retest. The failing case mixed valid MVP benchmarks with `000688.SH`, which is outside the current benchmark universe.

Root cause:

* Batch symbols were not disclosed with separate `requested_symbols`, `allowed_symbols`, and `rejected_symbols`.
* AgentLoop public metadata showed only the first tool symbol, so the block appeared to point at `000001.SH` even though the actual rejected symbol was `000688.SH`.

Fix:

* `agent/src/symbols/benchmark_policy.py` now canonicalizes batch symbols and validates each symbol against the benchmark universe.
* `agent/src/agent/loop.py` now exposes `requested_symbols`, `allowed_symbols`, `rejected_symbols`, and `benchmark_universe` in `_benchmark_policy`.
* Mixed batches are blocked as a whole; rejected symbols are not silently filtered out.

Commands run:

```bash
.venv/bin/python -m unittest agent.tests.test_benchmark_policy agent.tests.test_benchmark_policy_integration
```

Result:

* Passed.
* 51 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration
```

Result:

* Passed.
* 87 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration
```

Result:

* Passed.
* 56 tests.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* Passed.
* 46 tests.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests
```

Result:

* Passed.

Lightweight mock validation:

| Case | Provider called | Decision | Disclosure |
| --- | ---: | --- | --- |
| A-share all benchmark batch | 1 | `allow_benchmark` | `allowed_symbols=[000001.SH,399001.SZ,399006.SZ,000300.SH]` |
| A-share mixed batch | 0 | `block` | `allowed_symbols=[000001.SH,399001.SZ]`, `rejected_symbols=[000688.SH]` |
| US all benchmark batch | 1 | `allow_benchmark` | bare `SPY,QQQ,DIA` canonicalized to `.US` |
| US mixed batch | 0 | `block` | `allowed_symbols=[SPY.US]`, `rejected_symbols=[AAPL.US]` |
| Flag off A-share mixed batch | 0 | existing Symbol Guard behavior | no `_benchmark_policy` |

Boundary:

* Feature flag remains default off.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.
* Web UI retest after this fix was not run.

## 2026-07-09 a-stock-data Adapter Design Checks

Goal:

Readonly investigation and design only. No integration code was written.

Commands / checks:

```bash
pwd
git branch --show-current
git status --short
git log --oneline -8
git ls-files agent/.env agent/runs agent/sessions local_reports
```

Result:

* Current branch: `feature/bootstrap-local-setup`.
* Latest commit at start: `401369a fix: validate benchmark symbol batches`.
* No sensitive/runtime files tracked.

Readonly project files inspected:

* `agent/backtest/loaders/registry.py`
* `agent/src/market_data.py`
* A-share specialty tools under `agent/src/tools/`
* `agent/src/data_quality/`
* Guardrail docs under `docs_local/`

Readonly vendor discovery:

```bash
git clone --depth=1 https://github.com/simonlin1212/a-stock-data /Users/jz-home/Documents/Codex/workspace/Projects/Investment/_vendor_readonly/a-stock-data
```

Result:

* Readonly clone created outside the project repository.
* No vendor code copied into `Vibe-Trading`.
* No dependencies installed.
* No live public endpoint calls made.

Design output:

* Added `docs_local/A_STOCK_DATA_ADAPTER_DESIGN.md`.

Testing:

* No unit tests were run because this was a documentation-only design task.
* No Web UI or API research task was run.
* No live data smoke test was run.

Boundary:

* No business code changes.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No `a-stock-data` integration.
* No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-09 a-stock-data Financial Normalizer Phase B

Goal:

Build pure normalization helpers for a future `a-stock-data` A-share financial-statements adapter. This was a contract and test task only.

Files added:

* `agent/src/adapters/__init__.py`
* `agent/src/adapters/a_stock_data/__init__.py`
* `agent/src/adapters/a_stock_data/normalizer.py`
* `agent/tests/test_a_stock_data_normalizer.py`

Commands run:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration agent.tests.test_benchmark_policy agent.tests.test_benchmark_policy_integration
.venv/bin/python -m compileall -q agent/src agent/tests
```

Results:

* New a-stock-data normalizer tests: 20 tests passed.
* Anti-hallucination regression tests: 46 tests passed.
* Symbol / routing / benchmark regression tests: 194 tests passed.
* Compile check: passed.

Light pure-function validation:

| Case | Result |
| --- | --- |
| `report_date` rows | `ok=true`, `freshness_status=unknown`, `latest_data_date=2026-03-31` |
| `报告期` rows | `ok=true`, `freshness_status=unknown`, `latest_data_date=2026-03-31` |
| Empty rows | `ok=false`, `freshness_status=missing` |
| Explicit error payload | `ok=false`, `freshness_status=missing` |
| Rows without date | `ok=true`, `freshness_status=unknown`, warning `no_as_of_date` |

Boundary:

* No provider-chain changes.
* No loader changes.
* No `financial_statements_tool` integration.
* No Web UI changes.
* No live data calls.
* No dependency installation.
* No vendor code copied.
* No `agent/.env`, `agent/runs`, `agent/sessions`, or `local_reports` committed.

## 2026-07-09 a-stock-data Financial Statements Phase C Design

Goal:

Design the next integration step for `a-stock-data`: a feature-flagged fallback for `get_financial_statements`.

Files added:

* `docs_local/A_STOCK_DATA_FINANCIALS_INTEGRATION_PLAN.md`

Files updated:

* `docs_local/A_STOCK_DATA_ADAPTER_DESIGN.md`
* `docs_local/NEXT_TASKS.md`
* `docs_local/ROADMAP.md`
* `docs_local/CODEX_WORKLOG.md`
* `docs_local/CHANGELOG_LOCAL.md`
* `docs_local/TEST_REPORT.md`
* `docs_local/PRODUCT_BACKLOG.md`

Code/runtime status:

* No business code changed.
* No provider chain changed.
* No loader changed.
* No Web UI changed.
* No live endpoint test run.
* No dependency installed.

Validation:

* Documentation-only design task.
* Current `get_financial_statements` source routing was reviewed:
  * A-share: Eastmoney.
  * Hong Kong: Eastmoney HK F10.
  * US: SEC EDGAR.
* Existing pure `a-stock-data` financial normalizer helper was reviewed.

Recommended implementation gate:

Do not implement until the user approves the Phase C design. If approved, implement mock tests first and keep `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0` by default.

## 2026-07-09 a-stock-data Financial Statements Phase C Mock-first Hook

Goal:

Implement a feature-flagged, mock-first fallback hook for `get_financial_statements`.

Files added:

* `agent/src/adapters/a_stock_data/financials.py`
* `agent/tests/test_a_stock_data_financials_fallback.py`

Files changed:

* `agent/src/tools/financial_statements_tool.py`
* `agent/src/symbols/config.py`
* `agent/src/adapters/a_stock_data/__init__.py`

Feature flag:

```text
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER
```

Default:

```text
off
```

Commands run:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration agent.tests.test_benchmark_policy agent.tests.test_benchmark_policy_integration
.venv/bin/python -m compileall -q agent/src agent/tests
```

Results:

* a-stock-data normalizer + financial fallback tests: 51 tests passed.
* Data quality / anti-hallucination regressions: 46 tests passed.
* Symbol / routing / benchmark regressions: 194 tests passed.
* Compile check: passed.

Light mock validation:

| Case | Result |
| --- | --- |
| flag off + primary failure | fallback not called; original Eastmoney-style failure returned |
| flag on + primary success | fallback not called; primary result returned |
| flag on + `600519.SH` primary failure | fallback called; normalized `provider=a_stock_data` |
| flag on + `510300.SH` primary failure | fallback not called; ETF not eligible |
| flag on + `QQQ.US` primary failure | fallback not called; non-A-share not eligible |
| default fetch stub | returns `a_stock_data_live_fetch_not_implemented`; normalizes to missing |

Boundary:

* No live `a-stock-data` calls.
* No dependency installation.
* No provider-chain changes.
* No loader changes.
* No Web UI changes.
* No vendor code committed.
* No sensitive/runtime files committed.

## 2026-07-09 a-stock-data Controlled Live Smoke Test Design

Goal:

Design a controlled live smoke test for the a-stock-data financial fallback without running live requests.

Files added:

* `docs_local/A_STOCK_DATA_LIVE_SMOKE_TEST_PLAN.md`

Files updated:

* `docs_local/A_STOCK_DATA_FINANCIALS_INTEGRATION_PLAN.md`
* `docs_local/A_STOCK_DATA_ADAPTER_DESIGN.md`
* `docs_local/NEXT_TASKS.md`
* `docs_local/ROADMAP.md`
* `docs_local/CODEX_WORKLOG.md`
* `docs_local/CHANGELOG_LOCAL.md`
* `docs_local/TEST_REPORT.md`

Readonly discovery:

* Local readonly clone exists at `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/_vendor_readonly/a-stock-data`.
* Candidate endpoint: `sina_financial_report(code, report_type, num)`.
* Candidate source: Sina Finance `quotes.sina.cn`.
* Candidate raw shape: `list[dict]` with `报告期`.
* Required dependency for candidate: `requests`.
* Token/cookie requirement: none found for this endpoint.

Commands run:

* Git status and remote checks.
* Readonly `sed` / `rg` over project files and readonly vendor docs.

Not run:

* No live public endpoint request.
* No Web UI.
* No Agent task.
* No dependency installation.

Boundary:

* Documentation-only design task.
* No business code changes.
* No provider-chain or loader changes.
* No vendor code committed.
* No `local_reports` generated or committed.

## 2026-07-09 a-stock-data One-off Financial Live Smoke Script

Goal:

Implement and run one controlled live smoke script for the candidate Sina financial-statement endpoint.

Script added:

* `scripts/smoke_a_stock_data_financials.py`

Dependency check:

```bash
.venv/bin/python - <<'PY'
import requests
print(requests.__version__)
PY
```

Result:

* `requests 2.34.2`
* No dependency installation needed.

Compile check:

```bash
.venv/bin/python -m compileall -q scripts/smoke_a_stock_data_financials.py
```

Result:

* Passed.

Live smoke command:

```bash
.venv/bin/python scripts/smoke_a_stock_data_financials.py --symbols 600519.SH,300750.SZ --statements income --num 3 --timeout 15 --sleep 1.2 --output-dir local_reports
```

Result:

| Symbol | Statement | Status | Rows | Latest Date | Normalizer |
| --- | --- | --- | ---: | --- | --- |
| `600519.SH` | `income` | success | 3 | `2026-03-31` | ok |
| `300750.SZ` | `income` | success | 3 | `2026-03-31` | ok |

Local report:

```text
local_reports/a_stock_data_smoke_20260709_152952.json
```

This report is ignored by Git and was not committed.

Boundary:

* Did not read `agent/.env`.
* Did not require an LLM key.
* Did not enter AgentLoop.
* Did not modify `get_financial_statements`.
* Did not modify provider chain or loader.
* Did not modify Web UI.
* Did not install dependencies.
* Did not commit `local_reports`.

## 2026-07-09 a-stock-data Balance/Cashflow Follow-up Smoke

Goal:

Use the existing one-off script to validate the remaining two Sina statement mappings before any live fetch implementation.

Command:

```bash
.venv/bin/python scripts/smoke_a_stock_data_financials.py --symbols 600519.SH,300750.SZ --statements balance,cashflow --num 3 --timeout 15 --sleep 1.2 --output-dir local_reports
```

Result:

| Symbol | Statement | Status | Rows | Latest Date | Normalizer |
| --- | --- | --- | ---: | --- | --- |
| `600519.SH` | `balance` | success | 3 | `2026-03-31` | ok |
| `600519.SH` | `cashflow` | success | 3 | `2026-03-31` | ok |
| `300750.SZ` | `balance` | success | 3 | `2026-03-31` | ok |
| `300750.SZ` | `cashflow` | success | 3 | `2026-03-31` | ok |

Local report:

```text
local_reports/a_stock_data_smoke_20260709_153849.json
```

This report is ignored by Git and was not committed.

Boundary:

* No AgentLoop integration.
* No official fallback hook live implementation.
* No provider-chain or loader changes.
* No Web UI changes.
* No dependency installation.
* No `local_reports` committed.

## 2026-07-09 a-stock-data Phase D Live Fetch Behind Flag

Goal:

Implement the live Sina financial fetch inside `fetch_a_stock_financials(...)` while keeping the official fallback path feature-flagged and default off.

Files changed:

* `agent/src/adapters/a_stock_data/financials.py`
* `agent/tests/test_a_stock_data_financials_fallback.py`

Dependency check:

```bash
.venv/bin/python - <<'PY'
import requests
print(requests.__version__)
PY
```

Result:

* `requests 2.34.2`
* No dependency installation.

Unit and regression tests:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
```

Result:

* 56 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* 46 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer agent.tests.test_market_data_symbol_normalization agent.tests.test_symbol_intent_guard agent.tests.test_symbol_intent_guard_integration agent.tests.test_tool_routing_guard agent.tests.test_tool_routing_guard_integration agent.tests.test_benchmark_policy agent.tests.test_benchmark_policy_integration
```

Result:

* 194 tests passed.

Compile check:

```bash
.venv/bin/python -m compileall -q agent/src agent/tests scripts/smoke_a_stock_data_financials.py
```

Result:

* Passed.

Direct function smoke:

```bash
PYTHONPATH=agent .venv/bin/python - <<'PY'
from src.adapters.a_stock_data.financials import fetch_a_stock_financials
from src.adapters.a_stock_data.normalizer import normalize_a_stock_financials_result

for symbol in ("600519.SH", "300750.SZ"):
    for statement in ("income", "balance", "cashflow"):
        raw = fetch_a_stock_financials(symbol, statement_type=statement, num=3, timeout=15)
        norm = normalize_a_stock_financials_result(raw, symbol, source=raw.get("source"), upstream=raw.get("upstream"), statement_type=statement)
        quality = norm.get("_data_quality", {}).get(symbol, {})
        print(symbol, statement, raw.get("ok"), len(raw.get("data") or []), norm.get("ok"), quality.get("latest_data_date"), quality.get("freshness_status"), raw.get("error"))
PY
```

Result:

| Symbol | Statement | Raw OK | Rows | Normalizer OK | Latest Date | Freshness | Error |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `600519.SH` | `income` | true | 3 | true | `2026-03-31` | `unknown` | none |
| `600519.SH` | `balance` | true | 3 | true | `2026-03-31` | `unknown` | none |
| `600519.SH` | `cashflow` | true | 3 | true | `2026-03-31` | `unknown` | none |
| `300750.SZ` | `income` | true | 3 | true | `2026-03-31` | `unknown` | none |
| `300750.SZ` | `balance` | true | 3 | true | `2026-03-31` | `unknown` | none |
| `300750.SZ` | `cashflow` | true | 3 | true | `2026-03-31` | `unknown` | none |

Boundary:

* Did not read `agent/.env`.
* Did not need an LLM key.
* Did not run Web UI.
* Did not change provider chain or loader.
* Did not generate or commit `local_reports`.
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.

## 2026-07-11 a-stock-data Agent-level Financial Fallback Observation

Goal:

Verify whether the original Agent reasoning loop can discover and consume the
feature-flagged `a-stock-data` financial fallback in a controlled CLI
observation.

Script added:

```text
scripts/observe_agent_financial_fallback_research.py
```

Command:

```bash
.venv/bin/python scripts/observe_agent_financial_fallback_research.py --timeout 15 --max-iterations 8 --output-dir local_reports
```

Result:

```text
status=success
run_id=20260711_222201_15_854f55
iterations=2/8
financial_tool_calls=4
live_fallback_calls=4
provider=a_stock_data
source=sina_financial_report
latest_data_date=2026-03-31
```

Agent tool calls:

* `get_financial_statements 600519.SH income`
* `get_financial_statements 600519.SH balance`
* `get_financial_statements 600519.SH cashflow`
* `get_financial_statements 600519.SH indicators`

Acceptance:

* Agent called the official `get_financial_statements` tool.
* Primary provider failure was forced in-process.
* Fallback was used for `income`, `balance`, and `cashflow`.
* Final answer included Data Source Summary.
* Final answer included Source Warnings.
* Final answer mentioned the report date `2026-03-31`.
* Final answer disclosed that financial statements are not real-time data.
* No Symbol Clarification block occurred for explicit `600519.SH`.
* No benchmark policy path was involved.
* No asset-type routing block occurred.

Observed issue:

* The Agent also requested `indicators`. The current a-stock-data MVP does not
  support `indicators`, so this produced `a_stock_data_fallback_failed` in
  Source Warnings. This is expected under the current boundary and should be
  handled as a future product decision.

Boundary:

* Did not read or print `agent/.env`.
* Runtime LLM provider configuration was loaded by the project runtime only.
* Did not run Web UI.
* Did not modify provider chain or loader.
* Did not default-enable the adapter.
* Did not commit `local_reports`.

Regression tests:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
```

Result:

* 56 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* 46 tests passed.

Compile check:

```bash
.venv/bin/python -m compileall -q scripts/observe_agent_financial_fallback_research.py
```

Result:

* Passed.

## 2026-07-10 a-stock-data Phase F Direct/API Output Structure Observation

Goal:

Inspect whether the official `get_financial_statements` fallback output structure is suitable for report-layer Source Summary consumption.

Script added:

```text
scripts/inspect_get_financial_statements_fallback_output.py
```

Command:

```bash
.venv/bin/python scripts/inspect_get_financial_statements_fallback_output.py --symbols 600519.SH --statement-types income --timeout 15 --output-dir local_reports
```

Live requests:

* 2 live fallback requests in total.
* First run wrote the ignored JSON report under `local_reports`.
* Second run was a no-output pre-commit verification rerun.
* Symbol: `600519.SH`.
* Statement: `income`.

Local report:

```text
local_reports/get_financial_statements_fallback_output_inspection_20260709_160211.json
```

This file is ignored by Git and was not committed.

Observed compact summary:

| Field | Value |
| --- | --- |
| ok | true |
| symbol | `600519.SH` |
| statement_type | `income` |
| provider | `a_stock_data` |
| source | `sina_financial_report` |
| upstream | `a-stock-data` |
| row_count | 8 |
| latest_data_date | `2026-03-31` |
| freshness_status | `unknown` |
| has_data_quality | true |
| primary_error | `forced_primary_failure_for_output_inspection` |

Top-level keys:

```text
_data_quality, data, fallback, market, ok, period, provider, source, statement, statement_type, symbol, upstream
```

First row keys:

```text
eps, net_profit, raw, report_date, revenue
```

Warnings:

```text
primary_financials_unavailable
a_stock_data_fallback_used
```

Report-summary compatibility:

| Requirement | Result |
| --- | --- |
| has_provider | true |
| has_source | true |
| has_data_quality | true |
| has_latest_data_date | true |
| has_warnings | true |
| has_primary_error | true |

Regression tests:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
```

Result:

* 56 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* 46 tests passed.

Compile check:

```bash
.venv/bin/python -m compileall -q agent/src agent/tests scripts
```

Result:

* Passed.

Guard regression:

* Full guard/benchmark regression was not run in this round because no guard, benchmark, AgentLoop, provider-chain, loader, or Web UI code was modified.

Boundary:

* Did not read `agent/.env`.
* Did not need an LLM key.
* Did not run Web UI.
* Did not run AgentLoop research tasks.
* Did not change provider chain or loader.
* Did not install dependencies.
* Did not commit `local_reports`.
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.

## 2026-07-10 a-stock-data Phase G Controlled CLI / Tool-level Report Observation

Goal:

Observe whether fallback financial statements are disclosed correctly by the report-summary layer without running Web UI or AgentLoop.

Script added:

```text
scripts/observe_a_stock_financial_fallback_report_summary.py
```

Command:

```bash
.venv/bin/python scripts/observe_a_stock_financial_fallback_report_summary.py --symbols 600519.SH --statement-types income --timeout 15 --output-dir local_reports
```

Live requests:

* 1 live fallback request.
* Symbol: `600519.SH`.
* Statement: `income`.

Local report:

```text
local_reports/a_stock_financial_fallback_report_summary_observation_20260709_161128.json
```

This file is ignored by Git and was not committed.

Observed compact result:

| Field | Value |
| --- | --- |
| tool_result_ok | true |
| provider | `a_stock_data` |
| source | `sina_financial_report` |
| upstream | `a-stock-data` |
| statement_type | `income` |
| row_count | 8 |
| latest_data_date | `2026-03-31` |
| freshness_status | `unknown` |
| primary_error | `forced_primary_failure_for_report_observation` |

Data Source Summary:

* Present.
* Shows `get_financial_statements`.
* Shows `sina_financial_report`.
* Shows `row_count=8`.
* Shows `latest_data_date=2026-03-31`.

Source Warnings:

* Present.
* Includes `primary_financials_unavailable`.
* Includes `a_stock_data_fallback_used`.

Missing Data:

* Present because `freshness_status=unknown`.
* This is expected under the current generic report-summary rules.
* Rows exist and `latest_data_date` exists, so this is not a failed fallback.

No Estimate Warning:

* Not present.
* No false estimated market-fact warning was triggered by the mechanical summary.

Report Gate:

* Did not block.
* Reason: the prompt was not a market-data time-sensitive prompt, and the gate only evaluates `get_market_data` freshness metadata.

Compatibility:

| Check | Result |
| --- | --- |
| source_summary_has_a_stock_data | true |
| source_summary_has_sina | true |
| warnings_include_primary_unavailable | true |
| warnings_include_fallback_used | true |
| no_false_realtime_claim_detected | true |
| report_gate_does_not_block_valid_fallback | true |

Regression tests:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
```

Result:

* 56 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* 46 tests passed.

Compile check:

```bash
.venv/bin/python -m compileall -q agent/src agent/tests scripts
```

Result:

* Passed.

Guard regression:

* Full guard/benchmark regression was not run in this round because no guard, benchmark, AgentLoop, provider-chain, loader, or Web UI code was modified.

Boundary:

* Did not read `agent/.env`.
* Did not need an LLM key.
* Did not run Web UI.
* Did not run AgentLoop research tasks.
* Did not change provider chain or loader.
* Did not install dependencies.
* Did not commit `local_reports`.
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.

## 2026-07-09 a-stock-data Phase E Controlled Direct Tool Fallback Smoke

Goal:

Verify the official `get_financial_statements` tool path can use the live a-stock-data Sina financial fallback when the feature flag is enabled and the primary provider is forced to fail.

Script added:

```text
scripts/smoke_get_financial_statements_a_stock_fallback.py
```

Direct smoke command:

```bash
.venv/bin/python scripts/smoke_get_financial_statements_a_stock_fallback.py
```

Result:

```text
OK positive 600519.SH income: provider=a_stock_data source=sina_financial_report rows=8 latest=2026-03-31
OK positive 300750.SZ income: provider=a_stock_data source=sina_financial_report rows=8 latest=2026-03-31
OK positive 600519.SH balance: provider=a_stock_data source=sina_financial_report rows=8 latest=2026-03-31
OK positive 600519.SH cashflow: provider=a_stock_data source=sina_financial_report rows=8 latest=2026-03-31
OK negative 510300.SH income: fallback_called=False reason=etf_not_eligible_for_company_financials
OK negative QQQ.US income: fallback_called=False reason=not_a_share_market
OK negative 000001.SH income: fallback_called=False reason=index_not_eligible_for_company_financials
Summary: 7/7 cases passed
```

Regression tests:

```bash
.venv/bin/python -m unittest agent.tests.test_a_stock_data_normalizer agent.tests.test_a_stock_data_financials_fallback
```

Result:

* 56 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_data_freshness agent.tests.test_report_data_source_summary agent.tests.test_report_gate agent.tests.test_extended_data_quality agent.tests.test_no_estimate_guard
```

Result:

* 46 tests passed.

Compile check:

```bash
.venv/bin/python -m compileall -q scripts/smoke_get_financial_statements_a_stock_fallback.py
```

Result:

* Passed.

Boundary:

* Did not read `agent/.env`.
* Did not need an LLM key.
* Did not run Web UI.
* Did not run AgentLoop research tasks.
* Did not change provider chain or loader.
* Did not generate or commit `local_reports`.
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.

## 2026-07-11 Minimal Schema-producing Proof CLI

Goal:

Verify that mocked tool outputs can be converted into the MVP Research
Workspace structured report schema without Web UI, AgentLoop, provider calls,
or live data.

Files added:

```text
agent/src/reports/__init__.py
agent/src/reports/report_builder.py
agent/tests/test_report_builder.py
```

Implemented:

* `build_research_report(...)`
* `ReportBuildError`
* Offline schema builder for:
  * `research_meta`
  * `symbol`
  * `market_snapshot`
  * `financial_health`
  * `investment_memo`
  * `valuation`
  * `risks`
  * `data_confidence`
  * `limitations`

Test commands:

```bash
.venv/bin/python -m unittest agent.tests.test_report_builder
```

Result:

* 4 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_symbol_normalizer
```

Result:

* 12 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests/test_report_builder.py
```

Result:

* Passed.

Cases covered:

* Complete mock data produces a full schema.
* Missing financial data marks `financial_health` as `missing`.
* Provider failure lowers confidence and adds warnings.
* Invalid or unconfirmed symbol rejects schema generation.

Boundary:

* Did not call Sina, Eastmoney, or a-stock-data live endpoints.
* Did not run Web UI.
* Did not run AgentLoop.
* Did not modify provider chain, loader, or feature flags.
* Did not read or print `agent/.env`.

## 2026-07-11 Controlled Direct Tool Output Schema Proof

Goal:

Verify that official `FinancialStatementsTool().execute(...)` output can enter
the Research Report Schema Builder.

Files added:

```text
scripts/observe_direct_tool_schema_pipeline.py
agent/tests/test_direct_tool_schema_pipeline.py
```

Files changed:

```text
agent/src/reports/report_builder.py
```

Implementation:

* In-process enabled `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1`.
* Forced primary financial provider failure with a mock.
* Mocked a-stock-data fallback payloads for `income`, `balance`, and `cashflow`.
* Called official `FinancialStatementsTool().execute(...)`.
* Passed tool outputs into `build_research_report(...)`.
* Confirmed the schema includes `research_meta`, `symbol`, `market_snapshot`,
  `financial_health`, `data_confidence`, and `limitations`.

Observation command:

```bash
.venv/bin/python scripts/observe_direct_tool_schema_pipeline.py
```

Result:

```text
symbol=600519.SH
financial_status=available
statement_count=3
provider=a_stock_data
source=sina_financial_report
period_end_date=2026-03-31
warnings=['primary_financials_unavailable', 'a_stock_data_fallback_used']
```

Test commands:

```bash
.venv/bin/python -m unittest agent.tests.test_direct_tool_schema_pipeline
```

Result:

* 4 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_report_builder agent.tests.test_symbol_normalizer
```

Result:

* 16 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests/test_direct_tool_schema_pipeline.py scripts/observe_direct_tool_schema_pipeline.py
```

Result:

* Passed.

Cases covered:

* financial tool output -> schema success.
* financial fallback missing -> schema warning.
* index / ETF does not enter company financial schema.
* data quality missing -> schema warning.

Boundary:

* Did not call Sina, Eastmoney, or a-stock-data live endpoints.
* Did not run AgentLoop.
* Did not run Web UI.
* Did not modify provider chain, loader, or feature flags.
* Did not read or print `agent/.env`.

## 2026-07-12 Agent Trace Fixture to Research Schema Proof

Goal:

Prove that controlled Agent trace-like events can be collected offline and
converted into the Structured Research Report Schema.

Files added:

```text
agent/src/reports/trace_collector.py
agent/tests/test_trace_to_schema_pipeline.py
```

Files changed:

```text
agent/src/reports/__init__.py
```

Implementation:

* Added a pure/offline trace collector.
* Supports current `TraceWriter`-style events:
  * `type=tool_result`
  * `tool`
  * `status`
  * `result`
  * `type=answer`
* Supports design fixture-style events:
  * `event_type=tool_result`
  * `tool_name`
  * `result`
  * `event_type=final_answer`
* Collects market tool results into `market_result`.
* Collects `get_financial_statements` outputs into `financial_results`.
* Converts final answer text into interpretation placeholders.
* Preserves failed tool events and unknown events as warnings.
* Sends collected data into `build_research_report(...)`.

No observation script was added in this round. The unittest fixture is enough
for the offline proof and keeps the surface smaller.

Test commands:

```bash
.venv/bin/python -m unittest agent.tests.test_trace_to_schema_pipeline
```

Result:

* 7 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_report_builder agent.tests.test_direct_tool_schema_pipeline
```

Result:

* 8 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts
```

Result:

* Passed.

Cases covered:

* complete trace fixture -> schema success.
* missing market data -> market snapshot missing and warning.
* missing financial data -> financial health missing and warning.
* fallback financial data -> provider/source/fallback warnings preserved.
* failed tool event -> warning preserved.
* invalid / ambiguous symbol -> schema rejected.
* final answer missing -> facts still generate while investment memo remains
  placeholder/empty.

Boundary:

* Did not call live data.
* Did not run AgentLoop.
* Did not run Web UI.
* Did not modify provider chain, loader, or feature flags.
* Did not read or print `agent/.env`.
* Did not create or commit `local_reports`.

## 2026-07-12 Controlled Real Run Trace Observation Script

Goal:

Add a read-only observation script that can inspect an existing real
`trace.jsonl`, resolve offloaded trace fields, pass events into the
trace-to-schema collector, and emit a compact compatibility summary.

Files added:

```text
scripts/observe_real_trace_to_schema.py
agent/tests/test_real_trace_observation.py
```

Implementation:

* Script accepts:
  * `--trace-path`
  * `--run-id`
  * `--session-id`
  * `--symbol`
  * `--output-dir`
  * `--limit-events`
* Trace source priority:
  1. explicit `--trace-path`
  2. `agent/runs/<run_id>/trace.jsonl`
  3. `agent/sessions/<session_id>/trace.jsonl`
* If no trace source is supplied, the script does not guess.
* Uses `TraceWriter.read(..., resolve_offloads=True, resolve_fields={"result", "content", "prompt"})`.
* Does not write production `research_schema.json`.
* Optional output goes to ignored `local_reports`.
* Console output is compact and does not print full raw rows.

Test commands:

```bash
.venv/bin/python -m unittest agent.tests.test_real_trace_observation
```

Result:

* 7 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder agent.tests.test_direct_tool_schema_pipeline
```

Result:

* 15 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts
```

Result:

* Passed.

Cases covered:

* trace-path fixture -> observation summary success.
* missing trace path -> structured error.
* offloaded tool result payload -> resolved and handled.
* trace with no tool results -> `schema_generated=false` and warning.
* partial financial results -> partial schema and missing statement warnings.
* missing final answer -> schema still attempted.
* no run/session/trace source -> no guessing.

Boundary:

* Did not run AgentLoop.
* Did not run Web UI.
* Did not call live data.
* Did not read or print `agent/.env`.
* Did not modify provider chain, loader, or feature flags.
* Did not write production `agent/runs/<run_id>/artifacts/research_schema.json`.
* Did not create or commit `local_reports`.

## 2026-07-12 Controlled Historical Trace Observation

Goal:

Use an existing historical Agent run trace to verify:

```text
real trace -> observe_real_trace_to_schema.py -> trace_collector -> schema compatibility summary
```

Selected trace:

```text
agent/runs/20260705_170559_16_fc55fe/trace.jsonl
```

Selection reason:

* It is a run-scoped trace, which matches the preferred artifact path.
* It contains `get_market_data` and `get_financial_statements` tool results.
* It contains a final answer.
* It includes one offloaded field, which exercises the resolver path.

Command:

```bash
.venv/bin/python scripts/observe_real_trace_to_schema.py \
  --run-id 20260705_170559_16_fc55fe \
  --symbol 300750.SZ \
  --output-dir local_reports
```

Output:

```text
local_reports/real_trace_schema_observation_20260712_123508.json
```

The output file is ignored by Git and was not submitted.

Observation result:

* `event_count`: 53
* `tool_result_count`: 19
* `tool_names`:
  * `get_financial_statements`
  * `get_margin_trading`
  * `get_market_data`
  * `get_research_reports`
  * `get_sector_info`
  * `get_shareholder_count`
  * `get_stock_news`
  * `read_url`
  * `web_search`
* `has_market_data`: true
* `financial_statement_types_found`: `indicators`
* `has_final_answer`: true
* `schema_generated`: true
* `schema_sections_present`:
  * `research_meta`
  * `symbol`
  * `market_snapshot`
  * `financial_health`
  * `investment_memo`
  * `valuation`
  * `risks`
  * `data_confidence`
  * `limitations`
* `missing_sections`: none

Compatibility:

```text
can_read_trace: true
has_tool_results: true
has_required_financial_results: false
can_build_schema: true
suitable_for_future_artifact: true
```

Collector warnings:

* `market_data_quality_missing`
* `indicators_data_quality_missing`
* `balance_statement_missing`
* `cashflow_statement_missing`
* `income_statement_missing`
* Several non-schema tools were intentionally ignored by the collector, such as
  news, reports, sector info, web search, and URL reads.

Conclusion:

The observation proves that an existing historical real trace can be read and
converted into a structured schema compatibility summary. This specific trace
does not prove complete financial statement extraction because it only contains
`indicators`, not income, balance, and cashflow.

Follow-up:

Run the same observation against a future completed trace that includes all
three financial statement types before enabling production
`research_schema.json` artifact writing.

Regression commands:

```bash
.venv/bin/python -m unittest agent.tests.test_real_trace_observation
```

Result:

* 7 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder agent.tests.test_direct_tool_schema_pipeline
```

Result:

* 15 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts
```

Result:

* Passed.

Boundary:

* Did not run AgentLoop.
* Did not run Web UI.
* Did not call live data.
* Did not read or print `agent/.env`.
* Did not modify AgentLoop, provider chain, or loader.
* Did not write production `research_schema.json`.
* Did not commit `local_reports`.

## 2026-07-12 Controlled Real Agent Research Run - 300750.SZ

Goal:

Execute exactly one controlled real Agent research run and verify:

```text
Research Intent
  -> AgentLoop
  -> Tool Execution
  -> Trace
  -> observe_real_trace_to_schema
  -> Schema Completeness
```

Run command:

```bash
VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=1 \
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0 \
VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY=0 \
VIBE_TRADING_ENABLE_SHELL_TOOLS=0 \
.venv/bin/vibe-trading run --json --max-iter 20 -p "Analyze 300750.SZ as an investment research subject. Cover market snapshot, income statement, balance sheet, cash flow, financial health, risks, recent news and sector context. Use available tools and clearly state missing data."
```

Run result:

```text
status: success
run_id: 20260712_204249_68_4f64a5
run_dir: agent/runs/20260712_204249_68_4f64a5
```

Trace observation command:

```bash
.venv/bin/python scripts/observe_real_trace_to_schema.py \
  --run-id 20260712_204249_68_4f64a5 \
  --symbol 300750.SZ \
  --output-dir local_reports
```

Observation output:

```text
local_reports/real_trace_schema_observation_20260712_124625.json
```

The observation output was ignored by Git and not committed.

Trace:

* `trace_path`: `agent/runs/20260712_204249_68_4f64a5/trace.jsonl`
* `event_count`: 124
* `tool_result_count`: 42
* `has_final_answer`: true

Tool coverage:

| Capability | Tool evidence | Result |
| --- | --- | --- |
| market snapshot | `get_market_data` | PASS |
| income statement | `get_financial_statements` found `income` | PASS |
| balance sheet | `get_financial_statements` found `balance` | PASS |
| cash flow | `get_financial_statements` found `cashflow` | PASS |
| news | `get_stock_news` | PASS |
| research reports | `get_research_reports` | PASS |
| sector context | `get_sector_info` | PASS |

Schema:

* `schema_generated`: true
* `schema_sections_present`:
  * `research_meta`
  * `symbol`
  * `market_snapshot`
  * `financial_health`
  * `investment_memo`
  * `valuation`
  * `risks`
  * `data_confidence`
  * `limitations`
* `missing_sections`: none

Compatibility:

```text
can_read_trace: true
has_tool_results: true
has_required_financial_results: true
can_build_schema: true
suitable_for_future_artifact: true
```

Schema status:

```text
partial
```

Reason:

* Core trace-to-schema path passed.
* Required financial statement types were present.
* Data-confidence metadata still needs improvement:
  * market data was partial
  * latest market date was older than the run date
  * income/balance/cashflow data quality was missing
  * financial provider was not fully populated in the summary

Important safety finding:

The trace included `bash` tool results:

```text
bash status=ok: 1
bash status=error: 1
```

This is unexpected because the run was started with
`VIBE_TRADING_ENABLE_SHELL_TOOLS=0`. No code was changed during this task. This
must be investigated before productionizing Research Workspace or enabling any
remote workflow.

Runtime notes:

* `get_fund_flow` reported a connection-aborted fetch failure for `300750.SZ`.
* Duplicate tool calls were blocked by the existing duplicate-call guard.

Regression commands:

```bash
.venv/bin/python -m unittest agent.tests.test_real_trace_observation
```

Result:

* 7 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder agent.tests.test_direct_tool_schema_pipeline
```

Result:

* 15 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts
```

Result:

* Passed.

Boundary:

* Ran exactly one Agent research run.
* Did not modify AgentLoop.
* Did not modify provider chain.
* Did not modify loader.
* Did not modify Web UI.
* Did not read or print `agent/.env`.
* Did not write production `research_schema.json`.
* Did not commit `local_reports`.

## 2026-07-12 Fix Local CLI Shell Tool Opt-in

Goal:

Fix the local CLI `vibe-trading run` path so shell-capable tools are not
registered by default.

Root cause:

```text
vibe-trading run
  -> cli._legacy._run_agent(...)
  -> build_registry(..., include_shell_tools=True)
  -> BashTool registered
```

Fix:

* Added shared helper:
  `agent/src/tools/capabilities.py`.
* `shell_tools_enabled_from_env()` reads:
  `VIBE_TRADING_ENABLE_SHELL_TOOLS`.
* Default behavior is false.
* `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` keeps shell tools disabled.
* `VIBE_TRADING_ENABLE_SHELL_TOOLS=1` explicitly enables shell tools.
* Updated local legacy CLI `vibe-trading run` and CLI swarm live paths to use
  the helper instead of hardcoding shell tools on.
* Updated API shell gate to reuse the same helper.

Expected behavior:

| Environment | `bash` | `background_run` |
| --- | --- | --- |
| unset | not registered | not registered |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` | not registered | not registered |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS=1` | registered | registered |

Test commands:

```bash
.venv/bin/python -m unittest agent.tests.test_shell_tool_capability
```

Result:

* 6 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_report_builder agent.tests.test_direct_tool_schema_pipeline agent.tests.test_trace_to_schema_pipeline
```

Result:

* 15 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src agent/tests scripts
```

Result:

* Passed.

Boundary:

* Did not run a real AgentLoop.
* Did not call live data.
* Did not read or print `agent/.env`.
* Did not modify provider chain.
* Did not modify loader.
* Did not modify Web UI.
* Did not commit `agent/runs`.
* Did not commit `local_reports`.

## 2026-07-13 Controlled Real Research Run Security Re-validation

Goal: verify the local CLI shell-tool opt-in fix through one real `300750.SZ`
research run with `VIBE_TRADING_ENABLE_SHELL_TOOLS` explicitly unset.

Result:

* Run ID: `20260713_112141_18_fafffc`; status: success.
* Trace: `agent/runs/20260713_112141_18_fafffc/trace.jsonl`.
* Ignored observation: `local_reports/real_trace_schema_observation_20260713_032343.json`.
* 82 trace events; 24 tool results; final answer present.
* Market data plus `income`, `balance`, `cashflow`, and `indicators` were found.
* Schema compatibility summary generated with no missing top-level sections.
* `bash` and `background_run` were absent from all trace tool events.

Warnings:

* Market latest date was `2026-07-10`, older than the requested date
  `2026-07-13`.
* Financial per-statement `_data_quality` metadata was missing in this trace.
* One fund-flow request failed at the data-source network layer and was not
  hidden.

Regression:

* `agent.tests.test_shell_tool_capability`: 6 passed.
* `agent.tests.test_real_trace_observation agent.tests.test_trace_to_schema_pipeline agent.tests.test_report_builder`: 18 passed.
* `.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts`: passed.

Boundary:

* One real run only; no Web UI.
* No AgentLoop, provider-chain, loader, or Web UI code change.
* No `.env` read or printed; no runtime trace or local report committed.

## 2026-07-13 Financial Confidence Extractor Fixture-first Proof

Implemented:

* Added the pure `extract_financial_confidence(...)` function.
* Input: offline tool-like fixtures for income, balance, and cashflow.
* Output: `financial_health`, `data_confidence.financial_data`, and warnings.
* Unsupported `index` and `etf` asset types are rejected before confidence is
  generated.

Validation:

```bash
.venv/bin/python -m unittest agent.tests.test_financial_confidence_extractor
```

Result: 7 tests passed.

```bash
.venv/bin/python -m unittest agent.tests.test_report_builder agent.tests.test_trace_to_schema_pipeline agent.tests.test_direct_tool_schema_pipeline
```

Result: 15 tests passed.

```bash
.venv/bin/python -m compileall -q agent/src/reports agent/tests scripts
```

Result: passed.

Boundary:

* No live data, AgentLoop, Web UI, provider-chain, loader, or `.env` access.
* Extractor is not yet wired into `build_research_report`.

## 2026-07-13 Financial Confidence Integration Fixture Proof

Implemented:

* Connected the pure extractor to the report builder through a mechanical
  statement-type result index.
* Existing trace collection now produces statement-level financial confidence
  when it calls the builder.
* Complete core statements now use the explicit schema status complete; missing
  or failed core statements remain partial or missing.

Validation:

* Financial confidence integration tests: 6 passed.
* Extractor, report builder, trace, and direct-tool regressions: 22 passed.
* Compile check: passed.

Boundary:

* Fixture-only pipeline proof; no live data, AgentLoop, or Web UI.
* No provider-chain, loader, or production artifact change.
* No .env access and no runtime/local report committed.

## 2026-07-13 Fixture-only Research Schema Artifact Generator Proof

Implemented:

* Added an in-memory versioned research-schema artifact envelope generator.
* It consumes controlled trace fixture events through the existing collector and
  report builder.
* It returns complete, partial, or failed status with a report payload and safe
  error codes.
* Tests only serialize JSON to a TemporaryDirectory file named
  research_schema.json.

Validation:

* Artifact generator tests: 6 passed.
* Financial confidence integration, trace, and report builder regression tests:
  17 passed.
* Compile check: passed.

Boundary:

* No live data, AgentLoop, Web UI, production artifact path, provider-chain,
  loader, or .env access.

## 2026-07-13 Controlled Real Trace to Research Schema Artifact Observation

Implemented and observed:

* Added `scripts/observe_real_trace_to_artifact.py`, a read-only adapter from
  an existing trace directory to the in-memory artifact generator.
* Added four offline tests for invalid, empty, valid, and temporary-output
  trace observation cases.
* Read historical run `20260713_112141_18_fafffc` (82 events, 24 tool results)
  and wrote one observation-only artifact under ignored `local_reports/`.

Result:

* The artifact envelope was generated with schema version `1.0`, the original
  run id, a `partial` status, all report schema sections, and no generator
  errors.
* The trace contains market data, financial-tool calls, and a final answer.
* Its financial tool results are stored as text rather than structured
  statement payloads, so the collector cannot recover income, balance, or
  cashflow facts. Financial confidence correctly remains `missing` and records
  explicit statement-missing warnings.

Validation:

* Real-trace artifact observation tests: 4 passed.
* Artifact, financial-confidence, trace, and report-builder regression tests:
  23 passed.
* Compile check: passed.

Boundary:

* No new AgentLoop run, live data request, Web UI run, or production artifact
  write occurred.
* No `.env` access, provider-chain/loader change, or runtime/local report
  commit occurred.

## 2026-07-13 Fixture-first Structured Tool Result Serializer Proof

Implemented:

* Added a pure serializer for `get_market_data` and
  `get_financial_statements` JSON envelopes.
* The serializer separates verified `structured_payload`, bounded
  `human_summary`, provenance/data-quality metadata, and warnings.
* Rendered legacy text is not parsed for facts; it returns
  `structured_payload: null` with `legacy_unstructured_result`.

Validation:

* Serializer tests: 5 passed.
* Financial-confidence, artifact, trace, and report-builder regressions:
  23 passed.
* Compile check: passed.
* Serialized fixture payloads produced a complete research artifact with
  complete three-statement confidence and preserved a-stock-data provenance.

Boundary:

* Fixture-only proof. No AgentLoop, live data, Web UI, trace write, provider
  chain, loader, or `.env` access.

## 2026-07-13 Structured Tool Dual-write Fixture Proof

Implemented:

* Added a fixture-only helper that creates trace-compatible events containing
  both legacy `result` text and serializer-produced `structured_payload`.
* Updated the offline collector to prefer a valid `structured_payload` and
  retain its existing legacy `result` fallback.
* Covered financial and market success, serializer failure isolation, artifact
  completion, and unsupported-tool event integrity.

Validation:

* Dual-write tests: 5 passed.
* Report-builder, direct-tool schema, and trace pipeline regressions: 15
  passed.
* Compile check: passed.

Boundary:

* No AgentLoop, real tool, TraceWriter, provider-chain, loader, Web UI, live
  data, `.env`, runtime trace, or local report change.

## 2026-07-13 Default-off Financial Tool Runtime Dual-write MVP

Implemented:

* Added `VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE`, defaulting to disabled.
* Added a best-effort runtime enrichment helper for
  `get_financial_statements` only.
* AgentLoop keeps its existing legacy tool-context message and legacy trace
  result; it passes optional enrichment only after trace redaction.
* TraceWriter adds v1 fields only when enrichment is present. Small payloads
  stay structured in JSONL; large payloads use a safe sidecar.

Validation:

* Runtime dual-write tests: 5 passed.
* Dual-write, report-builder, and trace-pipeline tests: 16 passed.
* Direct-tool schema, serializer, artifact-generator, and confidence tests: 21
  passed.
* Compile check: passed.

Boundary:

* No real AgentLoop run, live data, Web UI, production artifact, provider-chain,
  loader, `.env` access, or runtime/local report commit.

## 2026-07-13 Controlled Real Research Run with Financial Runtime Dual-write

Run:

* Run id: `20260713_122810_49_b5872e`.
* Session id: none (local CLI run).
* Trace: `agent/runs/20260713_122810_49_b5872e/trace.jsonl`.
* Runtime flags: structured tool trace enabled; shell tools explicitly disabled.
* One real Agent research run was executed for `300750.SZ`; no additional Agent
  run was started.

Observation:

* The trace contains 63 events after completion and 16 tool-result events.
* Financial tool calls include income, balance, cashflow, and indicators.
* All four financial results have structured payloads; core statement payloads
  contain twelve Eastmoney periods each. No `bash` or `background_run` event
  appears.
* The initial legacy observation scripts did not resolve `structured_payload`
  sidecars, so they showed the legacy missing-financial view. A direct
  read-only resolver check confirmed payload availability.
* Schema/artifact generation remains `partial`: the primary financial envelope
  uses `data[symbol].periods`, while the current report builder expects a row
  list. Provider is absent, source is Eastmoney, upstream/fallback are absent,
  and data-quality/reporting-period metadata is incomplete.
* No final answer event was recorded, so the schema uses its final-answer
  placeholder and warning.

Validation:

* Runtime dual-write tests: 5 passed.
* Dual-write, report-builder, trace-pipeline, and direct-tool schema tests: 20
  passed.
* Compile check: passed.

Boundary:

* No code change, production artifact write, Web UI run, `.env` read, or
  runtime/local report commit occurred during this observation.

## 2026-07-13 Financial Statement Envelope Normalizer Fixture Proof

Implemented:

* Added a pure Eastmoney primary-envelope normalizer for
  `data[symbol].periods`.
* It mechanically converts existing period rows to the canonical row-list
  result shape used by report-builder and financial-confidence consumers.
* It maps only an existing `REPORT_DATE` field to `report_date` and emits
  warnings for absent periods or provenance.

Validation:

* Financial normalizer tests: 6 passed.
* Financial confidence integration, dual-write, and report-builder regressions:
  15 passed.
* Compile check: passed.
* Complete income/balance/cashflow fixtures produced complete confidence and a
  complete artifact.

Boundary:

* Fixture-only. No AgentLoop, tool, provider-chain, live data, Web UI, `.env`,
  runtime trace, or production artifact change.

## 2026-07-13 Financial Normalizer Report Consumer Integration Proof

Implemented:

* Added an offline financial pipeline between trace collection and report
  building.
* Structured Eastmoney `periods` envelopes normalize before confidence
  extraction; report_builder remains provider-envelope agnostic.
* Legacy canonical rows remain unchanged, provider records are not merged, and
  normalization failures become non-blocking collection warnings.

Validation:

* Financial normalizer pipeline tests: 5 passed.
* Financial normalizer, confidence integration, dual-write, and report-builder
  regressions: 21 passed.
* Compile check: passed.

Boundary:

* Offline only. No AgentLoop, real tool, provider-chain, live data, Web UI,
  `.env`, runtime trace, or production artifact change.

## 2026-07-13 Real Trace Observation Financial Pipeline Update

Implemented:

* Updated both read-only observation scripts to resolve offloaded
  `structured_payload` fields, in addition to legacy result/content/prompt
  fields.
* The already-integrated collector and financial pipeline now receive resolved
  structured financial payloads during schema and artifact observation.
* Added offline coverage for offloaded structured Eastmoney payloads, legacy
  rows, malformed envelopes, missing statements, and artifact compatibility.

Historical observation:

* Re-read the existing `300750.SZ` run trace only; no new Agent run, provider
  call, or Web UI session was started.
* The trace contains 81 events and 27 tool results. It exposes income, balance,
  cashflow, and indicators through structured financial payloads.
* Schema generation succeeds with every required section present. The artifact
  is correctly `partial`, not failed: the observed primary envelope has source
  `eastmoney` but no provider or upstream metadata, and the trace has no final
  answer event.
* Those gaps remain warnings (`provider_missing` and
  `final_answer_missing_from_trace`); no provenance, date, or financial fact
  was inferred by the observation path.

Validation:

* Real trace schema/artifact observation tests: 14 passed.
* Financial normalizer pipeline, financial confidence integration, and
  report-builder regressions: 15 passed.
* Compile check for reports, tests, and scripts: passed.

Boundary:

* No AgentLoop, real tool, provider-chain, loader, Web UI, or production
  artifact changes.
* No live data call or `.env` read.
* Observation files were written only to ignored `local_reports` and were not
  committed.

## 2026-07-13 Primary Financial Provenance Completion Contract Design

Designed:

* A verified metadata contract for primary financial structured trace results:
  provider, source, upstream, statement type, reporting period, row count,
  data quality, fallback status, and warnings.
* Producer precedence that accepts only explicit tool fields, adapter-owned
  execution context, or actual normalized rows for period/count facts.
* Consumer rules for trace collection, envelope normalization, confidence
  extraction, report building, and artifact generation.
* Explicit `complete`, `partial`, `missing`, and `failed` semantics so missing
  provenance remains visible rather than inferred.

Validation:

* Documentation-only review. No test, AgentLoop, provider, or live-data run
  was required or performed.

Boundary:

* No runtime, AgentLoop, tool, TraceWriter, provider-chain, loader, Web UI,
  `.env`, or production artifact change.

## 2026-07-13 Fixture-first Primary Financial Provenance Projection Proof

Implemented:

* Added a pure provenance projector and trace-enrichment adapter for primary
  and fallback financial structured payload fixtures.
* Added mechanical projection of provider, source, upstream, statement type,
  reporting period, row count, data quality, fallback status, primary error,
  and stable warnings.
* Preserved explicit payload fallback status, primary error, and warnings when
  the existing financial normalizer converts provider rows to canonical form.

Validation:

* Financial provenance projection tests: 10 passed.
* Financial normalizer, normalizer pipeline, confidence integration,
  serializer, dual-write, report-builder, and artifact-generator regressions:
  37 passed.
* Compile check for reports, tests, and scripts: passed.
* Complete primary fixtures produce complete financial confidence and complete
  artifacts; missing provenance fixtures remain partial with explicit warnings.

Boundary:

* Fixture-only. No runtime dual-write integration, AgentLoop, tool,
  TraceWriter, provider-chain, loader, Web UI, live data, `.env`, or production
  artifact change.

## 2026-07-13 Default-off Runtime Primary Financial Provenance Integration

Implemented:

* Integrated the provenance projector into the existing financial-only,
  default-off runtime dual-write helper.
* Passed current tool arguments and optional explicit execution metadata from
  the AgentLoop finalization boundary without changing tool execution, legacy
  text, LLM context, or Agent response.
* Preserved serializer failure isolation; projector failure now preserves the
  serialized structured payload and adds a trace-only warning.

Validation:

* Runtime provenance tests: 12 passed.
* Specified dual-write, provenance, normalizer, confidence, report, artifact,
  trace-schema, and observation regressions: 73 passed.
* Compile check for reports, tests, and scripts: passed.
* Fixture complete primary metadata produces complete confidence and artifact;
  missing provider/source remains partial with explicit warnings.

Boundary:

* No real AgentLoop run, live data request, Web UI run, `.env` read, production
  artifact write, runtime-file commit, provider-chain, loader, or tool change.
* The real primary path is not claimed complete: it still lacks explicit
  provider/upstream execution facts today.

## 2026-07-13 Controlled Real Financial Provenance Trace Re-validation

Executed exactly one controlled CLI research run for `300750.SZ` with
`VIBE_TRADING_ENABLE_STRUCTURED_TOOL_TRACE=1`,
`VIBE_TRADING_ENABLE_SHELL_TOOLS=0`, and the A-share financial fallback flag
enabled. No second run or retry was performed.

Observed trace: `agent/runs/20260713_161056_69_f0686d/trace.jsonl`.

Results:

* The trace contained 78 events, 25 tool results, and no `bash` or
  `background_run` tool call.
* `get_financial_statements` emitted structured sidecars and explicit metadata
  for `income`, `balance`, and `cashflow` (plus unsupported `indicators`).
* Each supported statement used the primary `eastmoney` path with
  `source=eastmoney`, `fallback_status.used=false`, 12 rows, and latest
  reporting period `2025-12-31`.
* The primary path did not expose an independent upstream fact. The metadata
  therefore retained `upstream` as empty and emitted
  `financial_upstream_missing`; this was not inferred by consumers.
* The schema observer resolved structured sidecars, found the three required
  statements, and successfully built a schema.
* The artifact observer produced every report section and rated financial
  health `complete`, but rated the artifact `partial` because the trace has no
  final answer and financial provenance still warns about missing upstream.

Validation:

* Financial provenance/transport/normalizer/observation suite: 71 passed.
* Shell capability suite: 6 passed.
* Compile check for `agent/src`, `agent/tests`, and `scripts`: passed.

Boundary:

* One real CLI run only; no Web UI, production artifact, provider-chain,
  loader, or code change.
* No `agent/.env` content was read or printed.
* Run/session files and `local_reports` observation outputs remain ignored and
  uncommitted.
