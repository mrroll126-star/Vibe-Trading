# Next Tasks

Status: Phase 0 completed. Trading-day readiness checks completed on 2026-07-05.

Basic local deployment works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable
* DeepSeek provider: verified
* Minimal native Agent research task: completed

## Recommended Task 1: Execute A-Share Trading-Day Real Usage Test

Priority: high.

Business value:

* Confirms whether the original Vibe-Trading A-share workflow is useful on a real trading day.
* Produces evidence for whether `a-stock-data` is actually needed and where.
* Captures data freshness, report quality, and missing-field gaps before code changes.

Suggested symbols:

* `600519.SH`
* `300750.SZ`

See:

* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`

Boundary:

* Test only.
* Do not ask for buy/sell advice.
* Do not integrate new providers.
* Keep shell tools disabled.

## Recommended Task 2: Symbol Normalization Design

Priority: high.

Business value:

* Builds on the SPY/SPY.US and A-share preflight findings.
* Reduces tool-routing ambiguity across US, A-share, HK, ETF, and index symbols.
* Creates a safer base before provider changes.

Boundary:

* Design first.
* No code changes without approval.

## Recommended Task 3: Plan `a-stock-data` Adapter From Real Gaps

Priority: high.

Business value:

* Uses tomorrow's records to target the adapter where the original project is weak.
* Avoids adding a large new source before we know the missing fields.

Boundary:

* Planning only unless separately approved.
* Do not replace original providers.

## Recommended Task 4: Fix Reports Loading / Runs Unknown If It Affects Use

Priority: medium.

Business value:

* Improves daily usability and auditability.
* Makes run history less confusing.

Boundary:

* Investigate only after user confirms bugfix work.

## Recommended Task 5: Custom Provider Plugin Framework Design

Priority: medium.

Business value:

* Creates a safe extension path for local providers while preserving upstream compatibility.
* Reduces future merge/rebase pain.

Boundary:

* Design only.
* Do not replace original providers.
* Do not change fallback chain yet.

## Recommended Task 6: LLM Router Design

Priority: medium.

Business value:

* Defines future task routing for DeepSeek, Qwen, Kimi, vision models, and Ollama.
* Keeps model cost and quality auditable.

Boundary:

* Design only.
* Do not implement before data-source and symbol basics are cleaner.

## Recommended Task 7: yfinance TLS Fix

Priority: low-medium.

Business value:

* Helps US/HK profile and yfinance-backed workflows.

Boundary:

* Diagnose before changing dependencies or provider code.

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
