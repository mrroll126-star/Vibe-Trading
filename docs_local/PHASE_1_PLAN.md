# Phase 1 Plan

Status: proposed plan. Do not implement without user confirmation.

## Phase 1 Goal

Build the foundation for long-term investment-research customization without breaking the upstream Vibe-Trading structure.

Principles:

* Keep upstream compatibility.
* Avoid replacing existing provider chains.
* Prefer adapters, extensions, smoke tests, and documentation before core changes.
* Keep security defaults: no committed secrets, no default shell tools, no public exposure.

## Task 1: Full US Data Source Smoke Test

Goal:

Run the full US data-source smoke test with explicit symbols:

* `AAPL.US`
* `SPY.US`
* `MSFT.US`
* `NVDA.US`
* `TSLA.US`
* `QQQ.US`

Purpose:

* Confirm stability of Yahoo direct, Sina, Eastmoney, yfinance, Stooq, AKShare, and key-gated providers where configured.
* Establish a US-equity data-source baseline before changing provider architecture.
* Produce an auditable report under ignored `local_reports/`.

Boundary:

* Do not modify provider chain.
* Do not add new data source.
* Do not change provider code.
* Test only.

## Task 2: Symbol Normalization Design

Goal:

Design one project-level symbol convention across:

* A-shares
* US stocks
* Hong Kong stocks
* ETFs
* Indexes

Input examples:

* `600519`
* `600519.SH`
* `SH600519`
* `sh.600519`
* `AAPL`
* `AAPL.US`
* `SPY`
* `SPY.US`
* `0700`
* `0700.HK`
* `HK.00700`

Recommended output format:

* A-share: `600519.SH`, `000001.SZ`
* US: `AAPL.US`, `SPY.US`
* Hong Kong: `0700.HK`

Phase 1 boundary:

* Design document first.
* No code changes until the user approves.
* Include examples, ambiguous cases, and failure behavior.

## Task 3: Custom Provider Plugin Framework Design

Goal:

Design a custom provider extension framework for local investment-research enhancements.

Principles:

* Do not replace original providers.
* Do not delete original fallback chain.
* Place custom providers in an extension/custom layer.
* Use a unified adapter contract.
* Each provider has a health check.
* Each provider has timeout handling.
* Each provider has structured error handling.
* Each provider has contract tests.

Design questions:

* Where should extension providers live?
* How should provider priority be configured?
* How should custom providers report health/status?
* How should local-only providers stay easy to rebase against upstream?

## Task 4: `a-stock-data` Adapter Planning

Goal:

Plan how to connect `simonlin1212/a-stock-data` as an A-share enhancement provider.

Boundary:

* Do not make it the only A-share data source.
* Do not replace original A-share providers.
* Start with an adapter.
* Start read-only.
* Focus on research data, not trading.
* Avoid major frontend changes.

Recommended planning output:

* Supported datasets.
* Symbol format mapping.
* Data contract mapping.
* Local cache implications.
* Failure and timeout behavior.
* Test plan.

## Task 5: LLM Router Design

Goal:

Design multi-model routing for investment research.

Initial routing concept:

* DeepSeek: main text reasoning.
* Qwen / DashScope: low-cost summaries and Chinese fallback.
* Kimi / Moonshot: long document reading.
* Qwen-VL / Kimi Vision: chart/image recognition design target.
* Ollama: local fallback.

Boundary:

* Design first.
* Do not assume vision route is already verified.
* Do not change runtime model routing until the single-provider workflow remains stable.

## Recommended Phase 1 Order

1. Full US data-source smoke test.
2. Symbol normalization design.
3. Custom provider plugin framework design.
4. `a-stock-data` adapter planning.
5. LLM router design.

Reason:

The native Agent workflow now works. The next highest-value improvement is to understand data-source stability and symbol normalization before adding new A-share data providers or multi-model routing.
