# Next Tasks

Status: Phase 0 completed. Phase 1 foundation work is in progress.

Basic local deployment works:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* CLI: executable
* DeepSeek provider: verified
* Current local DeepSeek model: `deepseek-v4-flash`
* Minimal native Agent research task: completed

## Priority Rule

Data Freshness & Anti-Hallucination Guardrails have higher priority than data-source expansion.

Reason:

* Adding more data sources does not solve hallucination by itself.
* If the LLM can still invent today's close, volume, turnover, fund flow, news, or financial metrics when data is missing, the product remains risky.
* Every future provider, including `a-stock-data`, should follow a freshness and source-failure contract.

Highest principle:

* LLM must not invent market data.

## Recommended Task 1: A-Share Trading-Day Real Usage Test

Priority: high.

Business value:

* Confirms whether the original Vibe-Trading A-share workflow is useful on a real trading day.
* Captures data freshness, report quality, missing-field gaps, and hallucination risk before code changes.
* Produces evidence for whether `a-stock-data` is needed and where.

Extra records to capture:

* Whether current-day data was retrieved.
* Data timestamp or data date.
* Which providers succeeded or failed.
* Whether the report disclosed missing data.
* Whether the report made factual claims without returned data.

See:

* `docs_local/A_SHARE_TRADING_DAY_TEST_PLAN.md`

Boundary:

* Test only.
* Do not ask for buy/sell advice.
* Do not integrate new providers.
* Keep shell tools disabled.

## Completed Phase 1 Item: Source Summary In Reports MVP

Status: completed on 2026-07-07.

Implemented:

* `agent/src/data_quality/report_summary.py`
* Mechanical Data Source Summary / Missing Data / Source Warnings appendix.
* Agent loop capture of `get_market_data` `_data_quality`.
* System prompt data truthfulness rules.
* `agent/tests/test_report_data_source_summary.py`

Remaining gap:

* This is not a hard report gate.
* Only `get_market_data` `_data_quality` is covered.
* Other tools such as `fund_flow`, `news`, and `research_reports` are not covered yet.

## Recommended Task 2: Time-sensitive Report Gate

Priority: high.

Business value:

* Prevents normal factual reports when critical current-day data is missing, stale, or unknown.
* Converts unsafe cases into a Data Insufficient Report.
* Protects questions about today, intraday, latest price, close, turnover, and percent change.

Design source:

* `docs_local/DATA_FRESHNESS_ANTI_HALLUCINATION_DESIGN.md`
* `docs_local/ARCHITECTURE_DECISIONS.md`

Boundary:

* Start with `get_market_data` quality only.
* Do not expand data sources.
* Do not rewrite the Web UI.
* Add acceptance tests for stale/missing/unknown current-day requests.

## Recommended Task 3: Extend Freshness To fund_flow / news / reports

Priority: high.

Business value:

* Today's fund flow, latest news, and research report facts are also high-risk factual claims.
* Extending metadata beyond OHLCV makes the report source summary more complete.

Boundary:

* Design per-tool contracts first.
* Do not change provider chain.
* Do not use `a-stock-data` yet.

## Completed Phase 1 Item: `get_market_data` Freshness Wrapper MVP

Status: completed on 2026-07-07.

Implemented:

* `agent/src/data_quality/freshness.py`
* `_data_quality` metadata in `agent/src/market_data.py`
* `agent/tests/test_data_freshness.py`

Validation:

* Unittest passed with 8 tests.
* Direct validation confirmed original per-symbol data is preserved.

Remaining gap:

* Reports do not yet consistently surface or obey `_data_quality`.

## Recommended Task 4: Source Summary In Reports

Priority: high.

Business value:

* Ensures provider failures are visible to the user, not hidden only in trace.
* Adds report sections such as Data Source Summary, Missing Data, and Source Failures.
* Reduces risk that the LLM turns missing data into a normal-looking conclusion.

Boundary:

* Start with report structure and prompt/gate behavior.
* Do not rewrite the entire Web UI.

## Recommended Task 5: Symbol Normalizer `get_market_data` Integration

Priority: medium-high.

Business value:

* Helps natural inputs like `600519`, `QQQ`, and `00700`.
* Should be integrated after freshness wrapper design so normalized symbols carry `raw_input` and warnings into the data contract.

Current files:

* `agent/src/symbols/normalizer.py`
* `agent/tests/test_symbol_normalizer.py`
* `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`

Boundary:

* Feature flag recommended.
* Start with `get_market_data` only.
* Do not broadly connect all tools.

## Recommended Task 6: `a-stock-data` Adapter Planning

Priority: medium-high, but after freshness guardrails.

Business value:

* Enhances A-share datasets where existing providers are weak.
* Should be planned from real trading-day gaps.

Boundary:

* Planning only unless separately approved.
* Do not replace original providers.
* Any adapter must follow the freshness contract before production research use.

## Deferred / Later

### Custom Provider Plugin Framework Design

Priority: medium.

Why later:

* Useful for maintainability, but freshness guardrails define the contract custom providers must satisfy.

### LLM Router Design

Priority: medium.

Why later:

* Important for cost and quality, but does not directly prevent data hallucination.

### Reports Loading / Runs Unknown

Priority: medium.

Why later:

* Product usability issue, but not the highest factual-risk item unless it blocks auditability.

### yfinance TLS Fix

Priority: low-medium.

Why later:

* Important for US/HK profile paths, but source failure disclosure is needed before fixing one provider.

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
