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

## Task 2: Data Freshness & Anti-Hallucination Guardrails

Goal:

Design and implement safeguards so the Agent does not invent market data when tools fail, return stale data, or return timestamp-unknown data.

Purpose:

* Prevent fabricated prices, close values, percent changes, turnover, volume, fund-flow numbers, news, announcements, and financial metrics.
* Require source failures and missing data to be visible in reports.
* Create a freshness contract that future providers, including `a-stock-data`, must satisfy.

Boundary:

* Design first.
* No new data source.
* No provider-chain replacement.
* No `a-stock-data` production integration until this guardrail path is planned.

Recommended implementation sequence:

1. `get_market_data` freshness wrapper.
2. Data Source Summary / Missing Data / Source Failures in reports.
3. Report gate for time-sensitive questions.
4. Extend freshness metadata to A-share specialty tools.
5. Require `a-stock-data` adapter to satisfy freshness contract.

Design document:

* `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`

## Task 3: Symbol Normalization Design

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

## Task 4: Custom Provider Plugin Framework Design

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

## Task 5: `a-stock-data` Adapter Planning

Goal:

Plan how to connect `simonlin1212/a-stock-data` as an A-share enhancement provider.

Boundary:

* Do not make it the only A-share data source.
* Do not replace original A-share providers.
* Start with an adapter.
* Start read-only.
* Focus on research data, not trading.
* Avoid major frontend changes.
* Do not integrate into production research workflows before freshness and anti-hallucination guardrails are implemented.

Recommended planning output:

* Supported datasets.
* Symbol format mapping.
* Data contract mapping.
* Local cache implications.
* Failure and timeout behavior.
* Test plan.

## Task 6: LLM Router Design

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

1. A-share trading-day real usage test.
2. Data Freshness & Anti-Hallucination Guardrails implementation planning.
3. `get_market_data` freshness wrapper.
4. Source summary in reports.
5. Symbol normalizer `get_market_data` integration.
6. `a-stock-data` adapter planning.
7. Custom provider plugin framework design.
8. LLM router design.

Reason:

The native Agent workflow now works. The next highest-value improvement is to prevent factual market-data hallucination before adding new A-share data providers or multi-model routing. More sources are useful only if their success, failure, staleness, and timestamps are carried into reports.
