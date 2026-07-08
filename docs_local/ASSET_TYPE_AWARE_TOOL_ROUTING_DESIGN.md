# Asset-type-aware Tool Routing Design

## 1. Problem Definition

The current system can now stop the LLM from silently rewriting an unclear symbol into a different ticker. It still does not systematically decide whether a selected tool is suitable for the asset type behind that symbol.

Risks:

* Calling stock-specific tools on an index.
* Calling shareholder count, margin trading, or financial-statement tools on an ETF.
* Calling A-share-only tools on US or HK assets.
* Confirming a symbol but still routing it into an unsuitable tool.
* Falling back to `web_search` / `read_url` after structured tools fail, then mixing web snippets with structured facts without clear source labels.

Core principle:

The agent must not use stock-specific tools on unsupported asset types without explicit routing policy.

Chinese operating rule:

Agent 不得在没有明确路由策略的情况下，把个股专项工具用于不支持的资产类型。

## 2. Current Routing Gap

Read-only investigation findings:

* Tool choice is mainly decided by the LLM from tool descriptions and the system prompt.
* `BaseTool` has `name`, `description`, `parameters`, `repeatable`, and `is_readonly`, but no structured market or asset-type compatibility metadata.
* `Symbol Normalizer` already returns `market`, `exchange`, `asset_type`, `needs_confirmation`, and warnings for many symbols.
* `Pre-tool Symbol Intent Guard` checks whether the tool symbol is traceable to the user's prompt. It does not check whether `get_sector_info`, `get_financial_statements`, or similar tools are compatible with `index`, `ETF`, or `fund`.
* `000001.SH` exposed this gap: `get_market_data` can fetch the index, but stock/sector-style tools can still be selected in a way that is semantically unclear.
* `web_search` and `read_url` are generic web tools and should not be blocked by symbol guard, but their results should be labeled as web / unstructured sources in final reports.

Current code locations:

| Area | File | Finding |
| --- | --- | --- |
| Tool registry | `agent/src/agent/tools.py` | No tool compatibility metadata. |
| AgentLoop pre-tool gate | `agent/src/agent/loop.py` | Symbol intent guard runs before tool execution. |
| System prompt routing | `agent/src/agent/context.py` | Routing guidance is text prompt based. |
| Symbol normalizer | `agent/src/symbols/normalizer.py` | Outputs `asset_type` for many normalized symbols. |
| Symbol intent guard | `agent/src/symbols/intent_guard.py` | Guards first-batch stock tools, but does not evaluate asset compatibility. |

## 3. Asset Type Definitions

MVP asset types:

* `stock`: listed operating company security.
* `index`: market or strategy index, not an operating company.
* `ETF`: exchange-traded fund or ETF-like security.
* `fund`: fund product that is not safely treated as an ETF in current rules.
* `unknown`: symbol was unresolved, ambiguous, or not classified.

Current expected examples:

| Input | Expected normalized symbol | Expected asset_type | Notes |
| --- | --- | --- | --- |
| `000001.SZ` | `000001.SZ` | `stock` | Ping An Bank. |
| `000001.SH` | `000001.SH` | `index` | Shanghai Composite; current explicit-symbol path may still carry warning from `000001` ambiguity. |
| `510300.SH` | `510300.SH` | `ETF` | A-share ETF prefix. |
| `159915.SZ` | `159915.SZ` | `ETF` | A-share ETF prefix. |
| `QQQ.US` | `QQQ.US` | `ETF` | US ETF recognized by current normalizer. |
| `SPY.US` | `SPY.US` | `ETF` | US ETF recognized by current normalizer. |
| `AAPL.US` | `AAPL.US` | `stock` | US stock. |
| `NVDA.US` | `NVDA.US` | `stock` | US stock. |
| `00700.HK` | `00700.HK` | `stock` | HK stock. |

Current gap:

The normalizer already detects `etf` for A-share ETF prefixes and `QQQ` / `SPY`. It does not yet provide a comprehensive index/fund universe, nor does AgentLoop consume asset type for tool routing.

## 4. Tool Compatibility Matrix

Initial design matrix based on current tool descriptions and implementation.

| Tool | stock | index | ETF | fund | unknown | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `get_market_data` | allow | allow | allow | maybe | maybe | Broad OHLCV market data through loaders. |
| `get_stock_news` | allow | warn | warn | warn | warn | A-share returns articles; US/HK returns Yahoo matches, not true articles. |
| `get_stock_profile` | allow US/HK | maybe | maybe | no | warn | Yahoo company/security profile; not reliable for A-share and known TLS failures. |
| `get_fund_flow` | allow, mainly A-share stock | warn | warn | no | block/warn | Per-symbol order flow; semantics for index/ETF need confirmation. |
| `get_sector_info` | allow A-share stock | block/warn | block/warn | no | block/warn | Membership mode is stock-sector membership; ranking mode is market-wide. |
| `get_research_reports` | allow A-share stock | block/warn | block/warn | no | block/warn | A-share sell-side coverage; usually company/security-specific. |
| `get_financial_statements` | allow stock | block | block/warn | no | block | Company financials only; index has no company statements. |
| `get_margin_trading` | allow A-share stock | block | warn/maybe | no | block | A-share margin rules may cover some ETFs, but provider semantics need confirmation. |
| `get_shareholder_count` | allow A-share stock | block | block | no | block | Company shareholder disclosure only. |
| `get_northbound_flow` | allow market context | allow market-level | maybe | no | warn | Market-wide Stock Connect flow, not per-stock flow. |
| `get_block_trades` | allow A-share stock | block | warn/maybe | no | block | Security-specific A-share block trades. |
| `search_symbol` | allow | allow | allow | allow | allow | Discovery only. |
| `web_search` | allow | allow | allow | allow | allow | Must be labeled web/unstructured. |
| `read_url` | allow | allow | allow | allow | allow | Must be labeled web/unstructured. |

MVP should avoid being too clever. For unclear cases, choose `warn`, `skip`, or `ask_for_confirmation` instead of guessing.

## 5. Routing Decision Types

Recommended decisions:

* `allow`: tool is compatible with the asset type and can be called.
* `warn`: tool may be useful, but final report must disclose compatibility risk.
* `block`: do not call the provider; return a structured Tool Routing Blocked result.
* `skip`: Agent may skip this tool and continue without treating it as an error.
* `ask_for_confirmation`: user must clarify the intended asset or whether the tool semantics are acceptable.

Examples:

* `get_market_data` + `000001.SH` index: `allow`.
* `get_financial_statements` + `000001.SH` index: `block`.
* `get_margin_trading` + `510300.SH` ETF: `warn` until provider semantics are confirmed.
* unknown asset type + stock-specific tool: `ask_for_confirmation` or `block`.

## 6. Proposed Routing Guard Architecture

Future module:

```text
agent/src/tools/routing_guard.py
```

Pure function:

```python
evaluate_tool_asset_compatibility(
    tool_name: str,
    symbol: str,
    market: str | None,
    asset_type: str | None,
    original_prompt: str | None = None,
) -> dict
```

Return shape:

```json
{
  "decision": "allow | warn | block | skip | ask_for_confirmation",
  "reason": "...",
  "tool_name": "...",
  "symbol": "...",
  "market": "...",
  "asset_type": "...",
  "warnings": ["..."],
  "matched_rule": "..."
}
```

Design requirements:

* Pure function only in the first implementation step.
* No provider calls.
* No loader changes.
* No Web UI changes.
* Deterministic decisions based on tool, market, and asset type.
* Explicit symbols should still pass symbol-intent guard; routing guard only decides tool compatibility.

## 7. Integration Point

Future AgentLoop order:

1. Symbol intent guard.
2. Symbol normalization / asset-type inference.
3. Asset-type tool routing guard.
4. Provider call.
5. Data quality wrapper.
6. Report summary / gate.

Recommended behavior:

* Run asset-type routing after the symbol intent guard, because an untraceable symbol should be clarified before compatibility is evaluated.
* If the tool has no symbol and is symbol-specific, block or ask for confirmation.
* If the tool is market-wide, do not require a symbol, but label it as market-level.
* If routing returns `block`, `skip`, or `ask_for_confirmation`, do not call the provider.
* Return structured result with `_tool_routing_guard` metadata.

## 8. Report Behavior

When routing guard returns `block`, `skip`, or `warn`, final reports should include:

```text
## Tool Routing Summary
```

Report should show:

* Tools actually called.
* Tools skipped because asset type was incompatible.
* Tools called with warnings.
* Tools that are web / unstructured sources.
* Tools blocked before provider execution.

The report must not silently replace blocked stock-specific data with web-search facts. If web sources are used, they must be labeled as web/unstructured and separated from structured market data.

## 9. MVP Scope

First implementation phase should cover the most obvious asset mismatches:

* `get_sector_info`
* `get_financial_statements`
* `get_shareholder_count`
* `get_margin_trading`
* `get_block_trades`

Why these first:

* They are easy to misuse on indexes and ETFs.
* They are mostly stock/company-specific.
* Blocking them does not disrupt the broad `get_market_data` path.

暂不覆盖:

* `web_search`
* `read_url`
* `search_symbol`
* `read_document`

These are discovery or unstructured-source tools. They should be labeled in reports, not blocked by asset routing.

## 10. Acceptance Tests

Pure-function acceptance tests:

| Case | Expected |
| --- | --- |
| `get_market_data` + `000001.SH` index | allow |
| `get_sector_info` + `000001.SH` index | block or warn |
| `get_financial_statements` + `000001.SH` index | block |
| `get_shareholder_count` + `000001.SH` index | block |
| `get_market_data` + `510300.SH` ETF | allow |
| `get_financial_statements` + `510300.SH` ETF | block or warn |
| `get_margin_trading` + `510300.SH` ETF | warn until provider semantics are confirmed |
| `get_stock_news` + `QQQ.US` ETF | allow or warn |
| `web_search` + any asset type | allow, `source_type=web_unstructured` |
| unknown asset type + stock-specific tool | ask_for_confirmation or block |
| `get_sector_info` + `600519.SH` stock | allow |
| `get_sector_info` + `000001.SH` index | no provider call after integration |

Integration acceptance tests after feature-flagged AgentLoop integration:

* Flag off: zero behavior change.
* Flag on + `000001.SH` + `get_market_data`: provider called.
* Flag on + `000001.SH` + `get_financial_statements`: provider not called; structured routing result returned.
* Flag on + `600519.SH` + `get_sector_info`: provider called.
* Flag on + `510300.SH` + company-specific tool: block/warn according to matrix.

Web UI retest focus:

* `000001.SH` today market overview.
* `510300.SH` ETF overview.
* `600519.SH` stock overview.
* `QQQ` ETF overview.
* Confirm `Tool Routing Summary` appears when tools are blocked or warned.

## 11. Priority Decision

Asset-type-aware tool routing must be designed before enabling Symbol Normalizer and Pre-tool Symbol Guard by default.

中文结论：

在默认开启 Symbol Normalizer / Pre-tool Symbol Guard 之前，应先完成资产类型感知的工具路由设计。

Default-enable view:

* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`: good candidate for default-on, but should wait for asset routing design and one implementation review.
* `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`: keep feature-flagged until more asset-type boundaries are tested.

## 12. Relationship to a-stock-data

`a-stock-data` adapter remains downstream.

Reason:

Adding more data sources before routing policy is clear will amplify wrong-tool risks. Each adapter and each tool should declare supported markets and asset types before it is used in default workflows.

Future adapter requirement:

Every custom provider should document:

* Supported market.
* Supported asset types.
* Supported fields.
* Time freshness semantics.
* Failure behavior.
* Whether it is stock-specific, index-capable, ETF-capable, or market-wide.

## 13. Pure Guard Implementation Status

Implemented on 2026-07-08:

* Module: `agent/src/tools/routing_guard.py`
* Function: `evaluate_tool_asset_compatibility(...)`
* Tests: `agent/tests/test_tool_routing_guard.py`

Current status:

* Pure function only.
* No AgentLoop integration.
* No provider calls.
* No loader changes.
* No Web UI behavior changes.
* No default feature flag changes.

Implemented MVP tools:

* `get_market_data`
* `get_sector_info`
* `get_financial_statements`
* `get_shareholder_count`
* `get_margin_trading`
* `get_block_trades`
* `get_stock_news`
* `web_search`
* `read_url`
* `search_symbol`

Validation summary:

* New routing guard unit tests passed.
* Symbol normalizer / symbol intent guard regression tests passed.
* Data freshness / report guard regression tests passed.
* Compile check passed.

Next step:

Feature-flagged AgentLoop integration. The future integration should run after Pre-tool Symbol Intent Guard and before provider execution.

## 14. Feature-flagged AgentLoop Integration Status

Implemented on 2026-07-08:

* Feature flag: `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD`
* Default: off
* AgentLoop integration point: after Pre-tool Symbol Intent Guard and before provider execution
* Integration tests: `agent/tests/test_tool_routing_guard_integration.py`

Runtime behavior:

* Flag off: zero behavior change.
* `allow`: provider/tool is called.
* `warn`: provider/tool is called and `_tool_routing_guard` metadata is appended to the tool result.
* `block`: provider/tool is not called; AgentLoop returns a structured `Tool Routing Blocked` result.
* `ask_for_confirmation`: provider/tool is not called; AgentLoop returns a structured `Tool Routing Requires Confirmation` result.

Important implementation note:

Routing inference does not modify tool arguments. It extracts the first symbol-like argument, infers market / asset type without network calls, then evaluates compatibility. `000001.SH` is treated as an index for routing decisions because the current normalizer still marks it as stock with an ambiguity warning.

Not yet done:

* Web UI asset-type routing retest.
* Default-enable decision.
* Tool Routing Summary section in final report.
