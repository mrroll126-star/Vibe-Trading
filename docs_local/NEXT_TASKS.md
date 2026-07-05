# Next Tasks

Status: updated after basic local deployment on 2026-07-05.

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

## Optional Next Step: US Data Source Smoke Test

Priority: medium.

Readiness:

* Backend dependencies are installed, so a script can be written and run next.
* yfinance is currently expected to fail.
* The script should isolate providers and continue after individual failures.

Recommended scope:

* `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, optional key-gated providers, and `local` if configured.
* Skip missing-key providers.
* Record provider status, elapsed time, row count, fields, and error summary.
* Do not alter provider chain or add `a-stock-data`.

## Not Approved Yet

* Do not integrate `a-stock-data`.
* Do not replace provider fallback chains.
* Do not enable shell tools.
* Do not expose services remotely.
* Do not develop trading execution features.
