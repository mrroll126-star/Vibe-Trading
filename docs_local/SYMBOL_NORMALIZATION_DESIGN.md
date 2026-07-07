# Symbol Normalization Design

Status: helper implemented; `get_market_data` first-stage integration implemented behind a disabled-by-default feature flag.

Date: 2026-07-05.

Scope: design a user-friendly symbol normalization layer for Phase 1. A pure helper now exists, but it is not wired into `get_market_data`, `get_stock_news`, Web UI, or any provider chain.

Update on 2026-07-07:

* `get_market_data` now has first-stage integration behind `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`.
* The flag is disabled by default.
* No other tools are integrated.
* Provider chains and loaders are unchanged.
* Chinese names still require confirmation and are not resolved automatically.
* Ambiguous symbols such as bare `000001` return warnings and are not forced into a provider call.

## 1. Why This Matters

Vibe-Trading works better when symbols are explicit:

* `SPY.US` routed better than bare `SPY`.
* `600519.SH` routed correctly to A-share tools.

Normal research users, however, naturally type:

* `QQQ`
* `600519`
* `00700`
* `贵州茅台`
* `腾讯`

The product should let users type natural inputs and internally convert them into a safe project convention before provider/tool calls.

## 2. Current Code Findings

### 2.1 Is There Existing Symbol Normalization?

There is no single project-wide `normalize_symbol()` function for user inputs.

Current behavior is split across several places:

* `agent/src/market_data.py`
  * `detect_source(code)` infers a data source from already-normalized symbol patterns.
  * It expects formats like `600519.SH`, `AAPL.US`, `00700.HK`, `BTC-USDT`.
  * Unknown formats default to `tushare`, which can misroute bare symbols.
* `agent/backtest/engines/_market_hooks.py`
  * `_detect_market(code)` classifies already-formatted codes into market types.
  * Unknown formats default to `a_share`.
* Loader-specific mapping functions exist, for example:
  * Yahoo: `AAPL.US -> AAPL`, `00700.HK -> 0700.HK`.
  * Eastmoney: requires suffixes for `.SH`, `.SZ`, `.BJ`, `.HK`, `.US`.
  * Tencent: requires `.SH` or `.SZ`.
  * AkShare: routes by `.SH`, `.SZ`, `.BJ`, `.HK`, `.US`.
  * BaoStock supports `601398.SH` and native `sh.601398`.
  * Mootdx accepts explicit `.SH/.SZ/.BJ` or bare six-digit A-share tickers.
* `agent/src/tools/symbol_search_tool.py`
  * Searches Eastmoney and Yahoo and returns candidate symbols in project convention.
  * This is a search/resolution tool, not a deterministic normalization gate.

Conclusion: the project has provider-specific symbol translation and a search tool, but not one auditable normalization contract applied before tools/loaders.

### 2.2 Loader Expected Formats

| Market | Loader / Layer | Expected Project Format | Notes |
| -- | -- | -- | -- |
| US | `market_data.detect_source` | `AAPL.US` | Bare `AAPL` does not match US regex and can fall through to `tushare`. |
| US | `yahoo_loader` / `yahoo_client` | `AAPL.US` | Provider maps to Yahoo `AAPL`. |
| US | `sina_loader` | `AAPL.US` | Requires `.US`; maps to bare ticker. |
| US | `eastmoney_loader` | `AAPL.US` | Uses Eastmoney search to resolve market prefix. |
| US | key-gated loaders | mostly `AAPL.US` or bare accepted internally | Safer to pass `.US`. |
| A-share | `market_data.detect_source` | `600519.SH`, `300750.SZ`, `430139.BJ` | Six digits plus suffix. |
| A-share | `tencent_loader` | `.SH` / `.SZ` | Does not accept bare symbols. |
| A-share | `eastmoney_loader` | `.SH` / `.SZ` / `.BJ` | Does not accept bare symbols. |
| A-share | `akshare_loader` | `.SH` / `.SZ` / `.BJ`; bare falls into A-share as default | Explicit suffix is safer. |
| A-share | `baostock_loader` | `600519.SH` or `sh.600519` | Native prefix accepted. |
| A-share | `mootdx_loader` | `.SH/.SZ/.BJ` or bare six digits | Bare accepted here only, not across all tools. |
| HK | `market_data.detect_source` | `00700.HK` or `700.HK` pattern | Regex accepts 3-5 digits plus `.HK`. |
| HK | `yahoo_client` | project `00700.HK`, Yahoo `0700.HK` | Yahoo drops to four-digit base. |
| HK | `eastmoney_client` | `00700.HK` | Eastmoney pads to five digits. |
| HK | `akshare_loader` | `00700.HK` | Pads to five digits internally. |

### 2.3 ETF / Index Handling

ETF:

* `agent/backtest/loaders/_symbol_utils.py` treats exchange-listed ETF / LOF prefixes as `15`, `16`, `50`, `51`, `52`, `56`, `58`.
* `akshare_loader` checks ETF before normal A-share because ETF symbols also end in `.SH` / `.SZ`.
* Recent preflight showed `510300.SH` and `159915.SZ` worked via Tencent and AkShare.

Index:

* Some index-like A-share codes, such as `000300.SH` and `399001.SZ`, can look like six-digit A-share symbols.
* Current market detection can classify six-digit `.SH/.SZ` as `a_share`.
* There is no user-facing disambiguation for `000001` as stock vs index.

### 2.4 Web UI And Agent Flow

The Web UI Agent page sends the textarea content directly to the backend session:

* Frontend `Agent.tsx` sends `api.sendMessage(session_id, finalPrompt)`.
* Backend session service passes natural-language prompt into the Agent loop.
* No Web UI symbol normalization step was found.

Agent tools expose parameter descriptions that encourage explicit symbols:

* `get_market_data`: examples include `AAPL.US`, `700.HK`, `BTC-USDT`.
* `get_stock_news`: requires suffix routing; bare `SPY` returns unsupported market.
* `get_stock_profile`: accepts US bare or `.US`, and HK `.HK`.

Risk: bare symbols depend on the LLM choosing the right tool arguments. If the LLM passes `SPY`, `get_market_data` may mark it unresolved or route it incorrectly.

## 3. Recommended User-Friendly Input Rules

The product should accept natural input and normalize into a structured result.

### 3.1 US Stocks And ETFs

User inputs:

* `QQQ`
* `SPY`
* `AAPL`
* `MSFT`
* `NVDA`
* `TSLA`
* `QQQ.US`
* `AAPL.US`

Recommended standard format:

* `QQQ.US`
* `SPY.US`
* `AAPL.US`

Rules:

* Pure English letters from 1 to 5 characters default to US ticker.
* Existing `.US` suffix is preserved and uppercased.
* If the same input has known multi-market ambiguity, return candidates and ask for confirmation.
* US ETFs such as `SPY` and `QQQ` should use `asset_type="etf"`, not `stock`, when known.

Examples:

| Raw Input | Normalized | Market | Asset Type | Confirmation |
| -- | -- | -- | -- | -- |
| `QQQ` | `QQQ.US` | `US` | `etf` | no |
| `SPY` | `SPY.US` | `US` | `etf` | no |
| `AAPL` | `AAPL.US` | `US` | `stock` | no |
| `AAPL.US` | `AAPL.US` | `US` | `stock` | no |

### 3.2 A-Shares

User inputs:

* `600519`
* `300750`
* `000001`
* `601318`
* `510300`
* `159915`
* `600519.SH`
* `300750.SZ`
* `SH600519`
* `SZ300750`
* `sh.600519`
* `sz.300750`

Recommended standard format:

* `600519.SH`
* `300750.SZ`
* `000001.SZ`
* `601318.SH`
* `510300.SH`
* `159915.SZ`

Rules:

* Already suffixed `.SH`, `.SZ`, `.BJ` is preserved and uppercased.
* `SH600519` and `sh.600519` normalize to `600519.SH`.
* `SZ300750` and `sz.300750` normalize to `300750.SZ`.
* Six-digit codes with common Shanghai stock prefixes default to `.SH`:
  * `600`, `601`, `603`, `605`, `688`.
* Six-digit codes with common Shenzhen stock prefixes default to `.SZ`:
  * `000`, `001`, `002`, `003`, `300`, `301`.
* Shanghai ETF prefixes default to `.SH`:
  * `510`, `511`, `512`, `513`, `515`, `516`, `518`.
* Shenzhen ETF / LOF prefix defaults to `.SZ`:
  * `159`.
* If code looks like an index, add warning or require context:
  * `000001` may mean 平安银行 (`000001.SZ`) or 上证指数 (`000001.SH` / index context).
  * `399001` likely requires index-specific handling.
* ETF and index should be marked with `asset_type`, not treated as ordinary stocks.

Examples:

| Raw Input | Normalized | Market | Asset Type | Confirmation |
| -- | -- | -- | -- | -- |
| `600519` | `600519.SH` | `CN` | `stock` | no |
| `300750` | `300750.SZ` | `CN` | `stock` | no |
| `510300` | `510300.SH` | `CN` | `etf` | no |
| `159915` | `159915.SZ` | `CN` | `etf` | no |
| `000001` | `000001.SZ` by default | `CN` | `stock` | yes if context says index or user intent is unclear |

### 3.3 Hong Kong Stocks

User inputs:

* `700`
* `0700`
* `00700`
* `9988`
* `09988`
* `00700.HK`
* `9988.HK`
* `HK.00700`

Recommended standard format:

* `00700.HK`
* `09988.HK`

Reason:

* `symbol_search_tool` formats HK symbols as five digits plus `.HK`.
* `eastmoney_client` pads HK codes to five digits.
* `akshare_loader` pads HK codes to five digits.
* `yahoo_client` maps project `00700.HK` to Yahoo `0700.HK` internally.

Rules:

* `.HK` suffix is preserved after padding the numeric code to five digits.
* `HK.00700` normalizes to `00700.HK`.
* Pure numeric 1-5 digit input can be HK only when:
  * user context explicitly says HK, or
  * known-name mapping says it is HK, or
  * there is no plausible A-share interpretation and product UX asks for confirmation.
* Six-digit numeric input defaults to A-share, not HK.
* `00700` with HK context becomes `00700.HK`.
* `00700` with CN context should not silently become HK; return warning or confirmation.

Examples:

| Raw Input | Context | Normalized | Market | Confirmation |
| -- | -- | -- | -- | -- |
| `00700` | HK | `00700.HK` | `HK` | no |
| `700` | HK | `00700.HK` | `HK` | no |
| `HK.00700` | any | `00700.HK` | `HK` | no |
| `9988` | HK | `09988.HK` | `HK` | no |
| `00700` | none | `00700.HK` if known mapping exists, else confirm | `HK` | maybe |

### 3.4 Chinese Names

First phase: design only, not implementation.

Examples:

* `贵州茅台` -> `600519.SH`
* `宁德时代` -> `300750.SZ`
* `腾讯` -> `00700.HK`
* `阿里巴巴` -> `BABA.US` / `09988.HK`, needs confirmation
* `中国平安` -> `601318.SH` / `02318.HK`, needs confirmation

Rules:

* Single-listing or locally curated unambiguous names can normalize automatically.
* Multi-listing or ambiguous names must return candidates and ask for confirmation.
* Name mapping should later depend on a local security master table, not hard-coded scattered dictionaries.
* `search_symbol` can be used as a resolver source, but deterministic local mappings should be preferred for common portfolio/watchlist names.

## 4. Internal Standard Structure

Future implementation should return a structured object, not just a string.

Example:

```json
{
  "raw_input": "600519",
  "normalized_symbol": "600519.SH",
  "market": "CN",
  "exchange": "SH",
  "asset_type": "stock",
  "name": "贵州茅台",
  "confidence": 0.95,
  "needs_confirmation": false,
  "candidate_symbols": [],
  "warnings": [],
  "source": "rule"
}
```

Field definitions:

| Field | Meaning |
| -- | -- |
| `raw_input` | Original user input, unmodified except trimming for storage. |
| `normalized_symbol` | Primary project-standard symbol to pass to tools/loaders. Empty when no safe primary exists. |
| `market` | Coarse market such as `US`, `CN`, `HK`, `CRYPTO`, `FX`, `UNKNOWN`. |
| `exchange` | Exchange/suffix such as `US`, `SH`, `SZ`, `BJ`, `HK`, or provider-native exchange when known. |
| `asset_type` | `stock`, `etf`, `index`, `fund`, `crypto`, `fx`, `future`, or `unknown`. |
| `name` | Display/security name when known. |
| `confidence` | 0-1 confidence score. Deterministic suffix rules can be high; ambiguous name search should be lower. |
| `needs_confirmation` | True when the system should ask the user to choose. |
| `candidate_symbols` | Ordered candidate objects when ambiguous. |
| `warnings` | Human-readable caveats, for example `000001 may also mean an index`. |
| `source` | Rule/data source used, such as `rule`, `security_master`, `search_symbol`, `user_context`. |

Candidate object:

```json
{
  "normalized_symbol": "09988.HK",
  "market": "HK",
  "exchange": "HK",
  "asset_type": "stock",
  "name": "阿里巴巴-W",
  "confidence": 0.82,
  "source": "security_master"
}
```

## 5. Where Bare Symbols Can Fail Today

Known likely failure points:

* `get_market_data(codes=["SPY"])`
  * `detect_source("SPY")` does not match `.US`, so it defaults to `tushare`.
  * Result can become `_unresolved`.
* `get_stock_news(code="SPY")`
  * The news tool routes only by suffix; bare `SPY` returns unsupported market.
* `get_market_data(codes=["600519"])`
  * Some loaders like Mootdx accept bare six digits, but the common `detect_source` does not choose Tencent because it requires `.SH/.SZ/.BJ`.
  * Unknown default can go to Tushare.
* `00700` without context
  * Could be interpreted as HK Tencent by a human, but six/non-six numeric rules need care.
* `000001`
  * Can mean 平安银行 (`000001.SZ`) or an index-like input depending on context.

## 6. Proposed Implementation Plan

No implementation in this round.

Recommended module location:

* Add shared module under `agent/src/symbols/normalizer.py` or `agent/src/symbols.py`.

Why not only `agent/backtest/loaders/`:

* Symbol normalization is not only a loader concern.
* It should serve Web UI, CLI, Agent tools, and future provider adapters.
* Loader-specific mapping should remain inside loaders after project-standard symbol is chosen.

Recommended package shape:

```text
agent/src/symbols/
  __init__.py
  normalizer.py
  models.py
  security_master.py
```

Future integration points:

1. CLI/helper command:
   * Add a diagnostic command or script to normalize inputs and print structured output.
2. Tool layer:
   * Apply normalization before `get_market_data`, `get_stock_news`, `get_stock_profile`, and A-share specialty tools.
3. Web UI:
   * Show recognized symbols/candidates near the prompt box or in a pre-submit hint.
4. Chinese name resolver:
   * Use local security master data first, then `search_symbol`.

Market master data:

* Needed for names, asset_type, ETF/index classification, and multi-listing ambiguity.
* First version can be a small local JSON/YAML/CSV for watchlist/common securities.
* Later version can sync from a proper security master source.

Cache:

* Deterministic rules do not need cache.
* `search_symbol` and remote name resolution should be cached with source/timestamp.
* Do not cache secrets.

How to avoid breaking providers:

* Normalize before provider calls.
* Keep existing provider-specific mapping functions unchanged.
* Treat normalization as an adapter layer that emits current project-standard symbols.
* Keep an escape hatch: already-valid symbols pass through unchanged.
* Log/return warnings instead of silently guessing low-confidence symbols.

Unit tests:

* Add pure unit tests for deterministic rules.
* Add no-network acceptance tests for listed examples.
* Add separate integration tests for `search_symbol` if remote providers are used.
* Include regression tests for `SPY`, `600519`, `00700`, `000001`, and Chinese names.

Rollout sequence:

1. Implement pure helper and tests only.
2. Add CLI/helper output for manual verification.
3. Wire tool layer with conservative behavior.
4. Add Web UI candidate hints.
5. Add Chinese name resolution using local security master.
6. Only then consider provider-chain or A-share adapter changes.

## 7. Open Decisions

| Decision | Recommended Default |
| -- | -- |
| HK standard width | Five digits, e.g. `00700.HK`, because project search and Eastmoney/AKShare use five digits. |
| Bare English ticker default | US, unless known ambiguity or user context overrides. |
| Bare six-digit numeric default | A-share, with prefix rules. |
| Bare 1-5 digit numeric default | Ask for context unless known HK mapping exists. |
| Chinese names | Design now; implement later with security master. |
| User confirmation | Required for multi-listing and known ambiguous symbols. |

## 8. Minimal Helper Implementation

Date: 2026-07-05.

Implemented files:

* `agent/src/symbols/__init__.py`
* `agent/src/symbols/normalizer.py`

What exists now:

* `NormalizedSymbol` dataclass.
* `normalize_symbol(raw, context=None)`.
* `normalize_many(inputs, context=None)`.
* `NormalizedSymbol.to_dict()`.
* `NormalizedSymbol.is_valid`.

What this implementation does:

* Pure rule-based normalization only.
* No network.
* No LLM.
* No data-source calls.
* No provider-chain changes.
* No Web UI changes.
* No tool-layer integration.

Supported now:

* US symbols such as `QQQ`, `SPY`, `AAPL`, `NVDA`, `QQQ.US`.
* A-share symbols such as `600519`, `300750`, `000001`, `SH600519`, `sh.600519`, `SZ300750`.
* HK symbols such as `700`, `0700`, `00700`, `9988`, `09988`, `00700.HK`, `HK.00700`.
* Chinese names are intentionally deferred and return `normalized_symbol=None` with `needs_confirmation=True`.

Important boundary:

Existing product behavior is unchanged until this helper is explicitly connected to tools or UI in a later approved task.

## 9. Integration Planning Status

Date: 2026-07-05.

Integration design has been documented in:

* `docs_local/SYMBOL_NORMALIZER_INTEGRATION_PLAN.md`

Current recommendation:

* Do not broadly connect the normalizer yet.
* Review A-share trading-day usage before deciding whether natural bare-code input is frequent enough to justify tool integration.
* If implementation is approved, start with `get_market_data` only.
* Use a disabled-by-default feature flag such as `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0` for the first integration.
* Keep explicit symbols such as `SPY.US`, `600519.SH`, `300750.SZ`, and `00700.HK` working exactly as before.
* Keep `get_stock_news` as the likely second integration.
* Defer A-share specialty tools, Chinese-name resolution, and Web UI hints until the first tool integration is proven safe.

## 10. Pre-tool Intent Guard Requirement

Date: 2026-07-08.

The Web UI bare-symbol retest showed that a tool-entry normalizer is not enough by itself.

Why:

* In the real Agent loop, the LLM can rewrite user input before calling tools.
* `000001` was converted to `000001.SZ` before `get_market_data` saw the raw input.
* `贵州茅台` was converted to `600519.SH` before the Chinese-name confirmation rule could run.

Design implication:

* Symbol Normalizer should remain disabled by default.
* Before default-enable, add a pre-tool Symbol Intent Guard that compares:
  * original user prompt
  * tool name
  * tool args
  * optional recent `search_symbol` results

New design document:

* `docs_local/PRE_TOOL_SYMBOL_INTENT_GUARD_DESIGN.md`

Priority rule:

The agent must not silently rewrite ambiguous user symbol intent.
