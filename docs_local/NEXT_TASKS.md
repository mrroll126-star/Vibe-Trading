# Next Tasks

Status: updated after LLM provider strategy design on 2026-07-05.

Basic local deployment now works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable

## Recommended Next Step 1: Configure One Main LLM Provider

Priority: high.

Business value:

* Gives the Agent a working reasoning model so the original Vibe-Trading research workflow can be tested.

Options:

* Direct DeepSeek as the preferred main text-reasoning model for Chinese investment research.
* Qwen/DashScope as a strong domestic alternative and future low-cost summary route.
* OpenRouter if one account should route multiple models.
* Ollama only as a local fallback or privacy-first test route.

Boundary:

* Create only local ignored config such as `agent/.env`.
* Do not commit real keys.
* See `docs_local/LOCAL_ENV_SETUP.md` for placeholder-only examples.
* Do not configure vision routing yet.
* Do not edit business code.

## Recommended Next Step 2: Run Minimal Research Task

Priority: high.

Business value:

* Confirms the unmodified Agent can start, use tools/data, and produce one useful research result.

Suggested test:

* Use `AAPL` or `SPY`.
* Use the prompt in `docs_local/MINIMAL_RESEARCH_TASK.md`.
* Do not ask for buy/sell advice.
* Keep shell tools disabled.

Why this comes first:

* The most important next proof is that the unmodified Agent can start, use tools/data, and write a useful research answer.
* After that baseline works, custom A-share integration will be much safer and easier to evaluate.

## Recommended Next Step 3: Design LLM Router

Priority: medium.

Business value:

* Separates main reasoning, cheap summaries, vision/chart OCR, long report reading, structured JSON, and local fallback.
* Keeps cost and quality auditable.

Reference:

* See `docs_local/LLM_PROVIDER_STRATEGY.md`.

Boundary:

* Design before implementation.
* Do not assume current project has already validated vision model calls.

## Recommended Next Step 4: Plan `a-stock-data` Adapter

Priority: medium.

Business value:

* Improves future A-share coverage after the original Agent workflow is proven.

Boundary:

* Planning document only until the user approves implementation.
* Do not replace existing provider chain.

## Recommended Next Step 5: Run Full US Data Source Smoke Test

Priority: high.

Business value:

* Expands the quick AAPL/MSFT check to all planned symbols and windows.
* Gives a better baseline before changing provider architecture.

Suggested command:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --timeout 15 --output-dir local_reports
```

Boundary:

* Results stay under ignored `local_reports/`.
* Missing API-key providers should remain skipped.

## Optional Later: Design Custom Provider Plugin Framework

Priority: medium.

Business value:

* Defines how future custom data adapters can be added without breaking upstream compatibility.
* Prepares a safer path for `a-stock-data` later.

Boundary:

* Design first.
* Do not implement `a-stock-data` yet.
* Do not change existing provider chain without explicit approval.

## Optional Later: Choose Whether To Fix yfinance TLS

Priority: high for US/HK equity research.

Observed issue:

```text
yfinance SSLError: curl: (35) TLS connect error ... OPENSSL_internal:invalid library (0)
```

Business value:

* yfinance is one of the no-key US/HK data fallbacks, but quick smoke test showed Yahoo direct, Sina, and Eastmoney already provide some US coverage.

Suggested approach:

1. Reproduce inside `.venv` with a tiny yfinance request.
2. Check `curl_cffi`, certificates, and OpenSSL linkage.
3. Do not change provider code until root cause is clear.

Current diagnostic result:

* yfinance import succeeds.
* `AAPL` 5d history fails with `curl_cffi` / libcurl TLS error.
* This should not block testing every US provider because direct Yahoo, Stooq, Sina, Eastmoney, and key-gated providers use different paths.

## Deferred: Tailscale Auth Dry Run

Priority: medium.

Business value:

* Moves toward remote access from the user's own devices.

Current status:

* Local ignored `agent/.env` now exists.
* `API_AUTH_KEY` has been generated.
* Shell tools are explicitly disabled.
* Tailscale is not installed or not available on `PATH`, so Tailnet dry run has not been executed.

Decision:

* Deferred for this project stage.
* The user keeps the Mac App Store variant of Tailscale because existing virtual domains and other projects depend on it.
* Remote control is temporarily handled through a remote desktop tool.
* Web UI remote exposure is not a current-stage goal.

Future re-enable conditions:

* Tailnet-only.
* `API_AUTH_KEY` configured.
* Shell tools disabled.
* No public exposure.
* No `agent/.env` commit.

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
