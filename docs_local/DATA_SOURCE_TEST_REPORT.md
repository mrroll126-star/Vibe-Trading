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
