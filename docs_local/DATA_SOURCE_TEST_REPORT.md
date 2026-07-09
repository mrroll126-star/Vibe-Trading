# Data Source Discovery Report

Status: read-only discovery only. No network calls and no real market requests were made.

## 1. Summary

* A-share provider status: multiple existing providers are already present. No-key providers include Tencent, Mootdx, Eastmoney, BaoStock, and AKShare. Tushare requires a token.
* US provider status: multiple existing providers are already present. No-key providers include Yahoo direct HTTP, Stooq, Sina, Eastmoney, yfinance, and AKShare. Tiingo, FMP, Finnhub, and Alpha Vantage require API keys.
* HK provider status: Eastmoney, Yahoo direct HTTP, yfinance, AKShare, and local data can work without API keys; Futu requires a local FutuOpenD gateway.
* Local provider status: existing provider supports CSV, Parquet, and DuckDB through `~/.vibe-trading/data-bridge/config.yaml`.
* Fallback mechanism: central fallback chains are in `agent/backtest/loaders/registry.py`. README and code agree on the main A-share, US, and HK fallback order; code is the source of truth.

## 2. Provider Files

| Market | Provider | File | Requires API Key | Free/No-Key Possible | Notes |
| ------ | -------- | ---- | ---------------- | -------------------- | ----- |
| A-share | tencent | `agent/backtest/loaders/tencent_loader.py` | No | Yes | First A-share fallback; public Tencent endpoint. |
| A-share | mootdx | `agent/backtest/loaders/mootdx_loader.py` | No | Yes | Tongdaxin TCP-style data; accepts suffix or bare 6-digit symbols. |
| A-share / US / HK | eastmoney | `agent/backtest/loaders/eastmoney_loader.py` | No | Yes | Public endpoint, shared client in `eastmoney_client.py`; may need throttling. |
| A-share | baostock | `agent/backtest/loaders/baostock_loader.py` | No | Yes | Supports `sh.601398` and `601398.SH` style symbols. |
| A-share / US / HK / more | akshare | `agent/backtest/loaders/akshare_loader.py` | No | Yes | Broad free fallback; dependency installed by base requirements. |
| A-share / futures / fund | tushare | `agent/backtest/loaders/tushare.py` | Yes | No | Requires `TUSHARE_TOKEN`; richer A-share source. |
| US / HK | yahoo | `agent/backtest/loaders/yahoo_loader.py` | No | Yes | Direct Yahoo chart endpoint; preferred for US auto-detection. |
| US | stooq | `agent/backtest/loaders/stooq_loader.py` | No | Yes | Daily EOD CSV; maps `AAPL.US` to Stooq lowercase form. |
| US | sina | `agent/backtest/loaders/sina_loader.py` | No | Yes | US daily bars through Sina endpoint. |
| US / HK / crypto | yfinance | `agent/backtest/loaders/yfinance_loader.py` | No | Yes | yfinance wrapper; maps project symbols to Yahoo format. |
| US | tiingo | `agent/backtest/loaders/tiingo_loader.py` | Yes | No | Requires `TIINGO_API_KEY`. |
| US | fmp | `agent/backtest/loaders/fmp_loader.py` | Yes | No | Requires `FMP_API_KEY`. |
| US | finnhub | `agent/backtest/loaders/finnhub_loader.py` | Yes | No | Requires `FINNHUB_API_KEY`. |
| US | alphavantage | `agent/backtest/loaders/alphavantage_loader.py` | Yes | No | Requires non-placeholder `ALPHAVANTAGE_API_KEY`. |
| HK / A-share | futu | `agent/backtest/loaders/futu.py` | Local gateway | Not without FutuOpenD | Requires FutuOpenD running locally, default 127.0.0.1:11111. |
| Any supported market | local | `agent/backtest/loaders/local_loader.py` | No | Yes, with local config | CSV, Parquet, DuckDB; explicit local does not fall back to network. |

## 3. Fallback Chains

The following chains come from `agent/backtest/loaders/registry.py`; use code as source of truth.

### A-share

* Order: `tencent` -> `mootdx` -> `eastmoney` -> `baostock` -> `akshare` -> `tushare` -> `local`

### US stocks

* Order: `yahoo` -> `stooq` -> `sina` -> `eastmoney` -> `yfinance` -> `tiingo` -> `fmp` -> `finnhub` -> `alphavantage` -> `akshare` -> `local`

### HK stocks

* Order: `eastmoney` -> `yahoo` -> `futu` -> `yfinance` -> `akshare` -> `local`

## 4. Symbol Normalization

* A-share examples:
  * `600519.SH`, `000001.SZ`, `430139.BJ` are common project formats.
  * BaoStock accepts native `sh.601398` / `sz.000001`.
  * Mootdx accepts `.SH/.SZ/.BJ` suffix or bare 6-digit tickers.
  * Tencent maps suffixes internally to `sh600519` or `sz000001`.
* US examples:
  * Loader auto-detection expects forms like `AAPL.US`.
  * Vendor calls often strip `.US` and use `AAPL`.
  * README notes swarm grounding can promote bare symbols like `NVDA` to `NVDA.US`.
  * `NASDAQ:AAPL` was not found as a native loader format in this read-only pass.
* HK examples:
  * Common project format is `00700.HK` or `700.HK`.
  * Futu maps to `HK.00700`.
  * Yahoo/yfinance use zero-padded `.HK` symbols internally when needed.
  * `HK.00700` appears as a Futu-specific vendor form, not the general project input format.
* Local examples:
  * `local:AAPL.US` explicitly routes to local configured data.

## 5. Existing Tests

* Test files found:
  * `agent/tests/test_market_data.py`
  * `agent/tests/test_market_data_tool.py`
  * `agent/tests/test_data_routing_sources_subset.py`
  * `agent/tests/test_market_detection.py`
  * `agent/tests/test_tencent_loader.py` was not found; Tencent likely covered indirectly.
  * `agent/tests/test_mootdx_loader.py`
  * `agent/tests/test_baostock_loader.py`
  * `agent/tests/test_akshare_loader.py`
  * `agent/tests/test_eastmoney_loader.py`
  * `agent/tests/test_sina_loader.py`
  * `agent/tests/test_stooq_loader.py`
  * `agent/tests/test_yfinance_loader.py` was not visible in the first 220 files, but yfinance behavior is covered by related market tests and README claims.
  * `agent/tests/test_finnhub_loader.py`
  * `agent/tests/test_fmp_loader.py`
  * `agent/tests/test_alphavantage_loader.py`
  * `agent/tests/test_tiingo_loader.py`
  * `agent/tests/test_futu_loader.py`
  * `agent/tests/test_local_loader.py`
  * `agent/tests/test_mcp_server_smoke.py`
  * `agent/tests/test_mcp_stdio_integration.py`
  * `agent/tests/test_mcp_sse_integration.py`
  * `agent/tests/test_mcp_streamable_http_integration.py`
* What they cover: loader behavior, registry behavior, market-data tool behavior, MCP smoke/integration paths, and security boundaries.
* What is missing for our local project: a repeatable local US data source smoke report that records provider-by-provider success, skipped status, elapsed time, row count, fields, and error summary.

## 6. Smoke Test Proposal

Next round, after dependencies are installed and the project can import successfully, add a low-risk script such as `scripts/smoke_test_us_data_sources.py`.

Proposed behavior:

1. Do not modify existing provider logic.
2. Test symbols: `AAPL.US`, `MSFT.US`, `NVDA.US`, `TSLA.US`, `SPY.US`, `QQQ.US`.
3. Check each US provider individually: `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, `tiingo`, `fmp`, `finnhub`, `alphavantage`, `akshare`, `local`.
4. Skip providers requiring missing keys instead of failing.
5. Use explicit timeouts.
6. Record `success`, `failed`, or `skipped`, plus elapsed time, returned fields, row count, error summary, and whether API key is required.
7. Write Markdown summary back to this document and JSON detail under an ignored directory such as `local_reports/`.
8. Before writing JSON reports, update `.gitignore` to ignore `local_reports/`.

## 7. yfinance Diagnostic

Date: 2026-07-05.

Result:

* yfinance import succeeds.
* yfinance version: 1.5.1.
* curl_cffi version: 0.15.0.
* `yf.Ticker("AAPL").history(period="5d")` fails.

Error summary:

```text
SSLError: Failed to perform, curl: (35) TLS connect error:
error:00000000:invalid library (0):OPENSSL_internal:invalid library (0)
```

Implication:

* This may affect the `yfinance` loader.
* It should not automatically block testing of `stooq`, direct `yahoo`, `sina`, `eastmoney`, `akshare`, or key-gated providers because they use different loader code paths.
* Full US data-source validation should record yfinance as failed if the issue remains.

## 8. Smoke Test Readiness

Current judgment: can start a low-risk US smoke test script next, with constraints.

Recommended scope:

* Provider-by-provider independent checks.
* Symbols normalized as `AAPL.US`, `MSFT.US`, `NVDA.US`, `TSLA.US`, `SPY.US`, `QQQ.US`.
* Providers requiring missing keys should be `skipped`, not `failed`.
* yfinance should be included but expected to fail until TLS is fixed.
* Direct Yahoo, Stooq, Sina, Eastmoney, and AKShare can be tested separately.
* Script should write JSON to an ignored local report directory only after `.gitignore` is checked or updated.

Not recommended:

* Do not integrate `a-stock-data` yet.
* Do not replace the existing provider chain.
* Do not change yfinance or curl dependency versions as part of the smoke test.

## 9. US Data Source Smoke Test Implementation

Date: 2026-07-05.

Scope:

* Added independent script: `scripts/smoke_test_us_data_sources.py`.
* The script calls existing loader classes directly.
* It does not change provider logic, provider order, fallback chains, symbol detection, or auth behavior.
* It writes local-only JSON and Markdown reports under `local_reports/`.
* `local_reports/` is ignored by Git and should not be committed.

Supported command:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --quick --timeout 10 --output-dir local_reports
```

Script behavior:

* Default symbols: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `SPY`, `QQQ`.
* Bare US tickers are normalized to project-style `.US` symbols, for example `AAPL` becomes `AAPL.US`.
* Default providers: `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, `tiingo`, `fmp`, `finnhub`, `alphavantage`, `akshare`, `local`.
* Missing API keys are recorded as `skipped`, not `failed`.
* Unsupported data types are recorded as `unsupported`.
* Each daily OHLCV fetch uses an explicit timeout.

Fields captured per record:

* market
* provider
* symbol
* normalized_symbol
* test_type
* status
* elapsed_ms
* rows_count
* returned_fields
* requires_api_key
* error_type
* error_summary
* timestamp

## 10. Quick Run Result

Command executed:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --quick --timeout 10 --output-dir local_reports
```

Result:

* Script completed successfully.
* JSON report generated locally under `local_reports/`.
* Markdown report generated locally under `local_reports/`.
* Reports are intentionally ignored by Git.

Quick mode tested:

* Symbols: `AAPL.US`, `MSFT.US`
* Test type: `daily_1mo`
* Quote/latest was recorded as `unsupported` because the existing loader interface exposes historical OHLCV, not a quote API.

Summary:

| Status | Count |
| -- | --: |
| success | 6 |
| failed | 6 |
| skipped | 10 |
| unsupported | 22 |

Provider result summary:

| Provider | Result |
| -- | -- |
| yahoo | Success for AAPL/MSFT 1-month daily bars. |
| sina | Success for AAPL/MSFT 1-month daily bars. |
| eastmoney | Success for AAPL/MSFT 1-month daily bars. |
| stooq | Failed with empty result for AAPL/MSFT in this run. |
| yfinance | Failed with empty result; stderr also reproduced curl/OpenSSL TLS errors. |
| akshare | Failed with empty result for AAPL/MSFT in this run. |
| tiingo | Skipped because `TIINGO_API_KEY` is not set. |
| fmp | Skipped because `FMP_API_KEY` is not set. |
| finnhub | Skipped because `FINNHUB_API_KEY` is not set. |
| alphavantage | Skipped because `ALPHAVANTAGE_API_KEY` is not set. |
| local | Skipped because `~/.vibe-trading/data-bridge/config.yaml` is not configured. |

Interpretation:

* The existing no-key US data path has at least three currently working options on this machine: direct Yahoo, Sina, and Eastmoney.
* yfinance remains unreliable in this environment until the curl/OpenSSL issue is fixed.
* Key-gated providers are ready to test later after the user provides real keys in ignored local environment files.
* The smoke test script is suitable as a repeatable baseline before any future US data-source changes.

## 11. Full US Smoke Test With Explicit Symbols

Date: 2026-07-05.

Command executed:

```bash
.venv/bin/python scripts/smoke_test_us_data_sources.py --symbols AAPL.US,MSFT.US,NVDA.US,TSLA.US,SPY.US,QQQ.US --timeout 15 --output-dir local_reports
```

Result files:

* JSON: `local_reports/us_data_sources_smoke_20260705_090237.json`
* Markdown: `local_reports/us_data_sources_smoke_20260705_090237.md`

These files are ignored by Git and were not committed.

Overall result:

| Status | Count |
| -- | --: |
| success | 40 |
| failed | 68 |
| skipped | 90 |
| unsupported | 330 |

Provider summary:

| Provider | Success | Failed | Skipped | Unsupported | Interpretation |
| -- | --: | --: | --: | --: | -- |
| yahoo | 18 | 0 | 0 | 30 | Best no-key US OHLCV provider in this run. |
| sina | 18 | 0 | 0 | 30 | Fastest successful no-key US OHLCV provider in this run. |
| eastmoney | 4 | 14 | 0 | 30 | Partially usable but unstable for explicit US symbols. |
| stooq | 0 | 18 | 0 | 30 | Returned no rows in this run. |
| yfinance | 0 | 18 | 0 | 30 | Still failed with curl/OpenSSL/TLS style errors. |
| akshare | 0 | 18 | 0 | 30 | Returned no usable US rows in this run. |
| tiingo | 0 | 0 | 18 | 30 | Skipped because key is not configured. |
| fmp | 0 | 0 | 18 | 30 | Skipped because key is not configured. |
| finnhub | 0 | 0 | 18 | 30 | Skipped because key is not configured. |
| alphavantage | 0 | 0 | 18 | 30 | Skipped because key is not configured. |
| local | 0 | 0 | 18 | 30 | Skipped because local data bridge is not configured. |

Daily OHLCV result:

* `yahoo`: 18/18 success across 1-month, 1-year, and 5-year daily checks.
* `sina`: 18/18 success across 1-month, 1-year, and 5-year daily checks.
* `eastmoney`: 4/18 success; AAPL succeeded for all three windows, MSFT 1-month succeeded, most others failed or returned no rows.
* `stooq`, `yfinance`, `akshare`: 0/18 success in this run.

Recommended short-term US provider order:

1. `yahoo` for default no-key US OHLCV.
2. `sina` as first fallback for no-key US OHLCV.
3. `eastmoney` only as opportunistic fallback, not primary.
4. Key-gated providers later after real keys are configured and tested.
5. Avoid relying on `yfinance` until TLS/curl issue is fixed.

## 12. a-stock-data Readonly Discovery

Date: 2026-07-09.

Readonly clone:

`/Users/jz-home/Documents/Codex/workspace/Projects/Investment/_vendor_readonly/a-stock-data`

Observed upstream:

* Repository: `https://github.com/simonlin1212/a-stock-data`
* Commit: `bcda405`
* Version described by README/SKILL: v3.3.0.
* License: Apache-2.0.

Project shape:

* Skill-style Markdown with embedded Python snippets.
* Not a conventional Python package in the current repository shape.
* Not an MCP server.
* Not an HTTP service.
* Dependencies described by upstream: `mootdx`, `requests`, `pandas`, `stockstats`.
* Most data sources are no-key; iwencai semantic search requires an API key.

Advertised A-share capabilities:

| Area | Examples |
| --- | --- |
| Market data | K-line, realtime quote, index, ETF, order book, tick trades |
| Research reports | Eastmoney stock reports, industry reports, PDF download, iwencai semantic search |
| Fund flow | Eastmoney minute and 120-day daily fund flow |
| News / announcements | Eastmoney news, global news, CNINFO announcements |
| Fundamentals | quarterly snapshot, F10, stock info, Sina statements |
| Sector / concepts | Eastmoney sector/concept membership, industry ranking |
| Northbound | THS realtime minute flow plus self-cached history |
| Margin / block trades / shareholder count | Eastmoney datacenter endpoints |
| Dragon tiger / lockup / dividend | Eastmoney datacenter endpoints |
| Limit-up / sentiment | Eastmoney pools and THS limit-up reasons |
| ETF options | Sina option contracts, T-quotes, Greeks, IV |
| Investor interaction / popularity | CNINFO IRM, THS hot list, Eastmoney hot rank |

Design conclusion:

Do not integrate this as a whole dependency. Treat it as a candidate source of endpoint knowledge and field mappings. Start with a narrow, feature-flagged tool-level adapter design.

Recommended MVP:

* A-share financial statements fallback.
* No provider-chain replacement.
* No live endpoint calls until pure normalization helpers and tests exist.
* All output must include `_data_quality` and be visible in Source Summary.

Still unknown:

* Exact endpoint stability for this machine.
* Per-endpoint field completeness.
* Which fields always contain reliable dates.
* Whether each endpoint supports batch symbols.
* How much attribution is required if code snippets are adapted.
