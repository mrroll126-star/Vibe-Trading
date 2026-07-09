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
