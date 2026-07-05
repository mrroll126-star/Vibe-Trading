# Next Tasks

Status: updated after US data-source smoke test on 2026-07-05.

Basic local deployment now works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable

## Recommended Next Step 1: Configure LLM Provider Safely

Priority: high.

Business value:

* Enables real agent research workflows instead of only health/UI checks.

Options:

* Local Ollama, no cloud API key.
* OpenRouter/OpenAI/DeepSeek/etc. with API key.
* OpenAI Codex ChatGPT OAuth using `vibe-trading provider login openai-codex`.

Boundary:

* Create only local ignored config such as `agent/.env`.
* Do not commit real keys.
* See `docs_local/LOCAL_ENV_SETUP.md` for placeholder-only examples.

## Recommended Next Step 2: Investigate yfinance TLS Failure

Priority: high for US/HK equity research.

Observed issue:

```text
yfinance SSLError: curl: (35) TLS connect error ... OPENSSL_internal:invalid library (0)
```

Business value:

* yfinance is one of the no-key US/HK data fallbacks.

Suggested approach:

1. Reproduce inside `.venv` with a tiny yfinance request.
2. Check `curl_cffi`, certificates, and OpenSSL linkage.
3. Do not change provider code until root cause is clear.

Current diagnostic result:

* yfinance import succeeds.
* `AAPL` 5d history fails with `curl_cffi` / libcurl TLS error.
* This should not block testing every US provider because direct Yahoo, Stooq, Sina, Eastmoney, and key-gated providers use different paths.

## Recommended Next Step 3: Prepare Tailscale Auth Dry Run

Priority: medium.

Business value:

* Moves toward remote access from the user's own devices.

Boundary:

* Do not expose services yet.
* First create placeholder-only `.env.example.local` if approved.
* Then configure real `API_AUTH_KEY` only in ignored local `agent/.env`.

## Completed: US Data Source Smoke Test

Status: completed as a low-risk feature.

What exists now:

* Script: `scripts/smoke_test_us_data_sources.py`.
* Local ignored reports: `local_reports/`.
* Quick command:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --quick --timeout 10 --output-dir local_reports
```

Latest quick result:

* Working in quick test: `yahoo`, `sina`, `eastmoney`.
* Failed or empty in quick test: `stooq`, `akshare`, `yfinance`.
* Skipped because keys/config are missing: `tiingo`, `fmp`, `finnhub`, `alphavantage`, `local`.

Recommended follow-up:

* Keep the script as a baseline.
* Do not change provider logic until repeated runs confirm which failures are stable.
* Fix yfinance TLS separately if yfinance is important for US/HK coverage.

## Not Approved Yet

* Do not integrate `a-stock-data`.
* Do not replace provider fallback chains.
* Do not enable shell tools.
* Do not expose services remotely.
* Do not develop trading execution features.
