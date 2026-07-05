# Next Tasks

Status: Phase 0 completed. Phase 1 is ready for user confirmation.

Basic local deployment works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable
* DeepSeek provider: verified
* Minimal native Agent research task: completed

## Phase 1 Recommended Task 1: Full US Data Source Smoke Test

Priority: high.

Business value:

* Validates US data-source reliability with explicit project-style symbols.
* Produces a baseline before changing provider architecture.
* Helps decide which providers should be preferred for US research.

Suggested symbols:

* `AAPL.US`
* `SPY.US`
* `MSFT.US`
* `NVDA.US`
* `TSLA.US`
* `QQQ.US`

Suggested command:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --symbols AAPL.US,SPY.US,MSFT.US,NVDA.US,TSLA.US,QQQ.US --timeout 15 --output-dir local_reports
```

Boundary:

* Test only.
* Do not modify provider chain.
* Results stay under ignored `local_reports/`.

## Phase 1 Recommended Task 2: A-Share Trading-Day Validation

Priority: high.

Business value:

* Confirms whether the original Vibe-Trading A-share workflow works on a real trading day.
* Tests current-day data freshness and A-share tool behavior before adding any new provider.
* Gives a safer baseline before planning `a-stock-data`.

Suggested symbols:

* `600519.SH`
* `300750.SZ`
* `000001.SZ`

Boundary:

* Test only.
* Use existing providers.
* Do not integrate `a-stock-data`.
* Do not ask for buy/sell advice.

See:

* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`

## Phase 1 Recommended Task 3: Symbol Normalization Design

Priority: high.

Business value:

* Fixes a real issue exposed by the minimal SPY task: bare `SPY` caused partial data-tool routing failures.
* Creates a stable convention for A-share, US, HK, ETF, and index symbols.

Output:

* Design document first.
* No code changes without approval.

## Phase 1 Recommended Task 4: Custom Provider Plugin Framework Design

Priority: medium.

Business value:

* Creates a safe extension path for local providers while preserving upstream compatibility.
* Reduces future merge/rebase pain.

Boundary:

* Design only.
* Do not replace original providers.
* Do not change fallback chain yet.

## Phase 1 Recommended Task 5: `a-stock-data` Adapter Planning

Priority: medium.

Business value:

* Prepares A-share enhancement while keeping original Vibe-Trading providers intact.

Boundary:

* Planning only.
* No implementation yet.
* No trading functionality.

## Phase 1 Recommended Task 6: LLM Router Design

Priority: medium.

Business value:

* Defines future task routing for DeepSeek, Qwen, Kimi, vision models, and Ollama.
* Keeps model cost and quality auditable.

Boundary:

* Design only.
* Do not implement before data-source and symbol basics are cleaner.

## Deferred / Later

### yfinance TLS

Status: unresolved.

Why later:

* It is important for US/HK research, but quick smoke test showed Yahoo direct, Sina, and Eastmoney already provide some coverage.
* Diagnose before changing dependencies or provider code.

### Tailscale Web Dry Run

Status: deferred by user decision.

Current remote-control path:

* Remote desktop tool.

Future re-enable conditions:

* Tailnet-only.
* `API_AUTH_KEY`.
* Shell tools disabled.
* No public exposure.
* No `agent/.env` commit.

## Not Approved Yet

* Do not integrate `a-stock-data`.
* Do not replace provider fallback chains.
* Do not enable shell tools.
* Do not expose services remotely.
* Do not develop trading execution features.
