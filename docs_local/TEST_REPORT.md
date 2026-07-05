# Test Report

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
