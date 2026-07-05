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

## Recommended Next Step 3: Prepare Tailscale Auth Dry Run

Priority: medium.

Business value:

* Moves toward remote access from the user's own devices.

Boundary:

* Do not expose services yet.
* First create placeholder-only `.env.example.local` if approved.
* Then configure real `API_AUTH_KEY` only in ignored local `agent/.env`.

## Not Approved Yet

* Do not integrate `a-stock-data`.
* Do not replace provider fallback chains.
* Do not enable shell tools.
* Do not expose services remotely.
* Do not develop trading execution features.
