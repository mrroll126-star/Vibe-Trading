# Pre-tool Symbol Intent Guard Design

## 1. Problem Definition

The current `get_market_data` symbol normalizer works at the tool-entry level. It can normalize or block the symbol values that are passed into `get_market_data`.

The Web UI bare-symbol retest showed a different risk: in real Agent runs, the LLM or `search_symbol` may rewrite the user's original symbol intent before `get_market_data` is called.

Examples from the Web UI retest:

| User input | Tool argument observed | Risk |
| -- | -- | -- |
| `000001` | `000001.SZ` | The Agent silently chose Ping An Bank even though the user could have meant the Shanghai Composite index. |
| `贵州茅台` | `600519.SH` | The Agent mapped a Chinese name to a ticker before the normalizer could ask for confirmation. |

Risk:

* `000001` can be silently interpreted as `000001.SZ`, while the user may mean `000001.SH`.
* Chinese names such as `贵州茅台` may appear obvious today, but the general class of Chinese-name inputs needs confirmation or auditable search metadata.
* Future multi-listing names or similar names may be mapped incorrectly.
* If the chosen symbol returns fresh data, the final report can look credible while analyzing the wrong object.

Core principle:

> The agent must not silently rewrite ambiguous user symbol intent.

中文：

> Agent 不得静默改写存在歧义的用户标的意图。

## 2. Risk Scenarios

### 000001

Possible meanings:

| Meaning | Symbol |
| -- | -- |
| Ping An Bank | `000001.SZ` |
| Shanghai Composite index | `000001.SH` |

If the user writes only `000001`, the system must require clarification or at least produce an explicit blocking result before calling a provider.

It should not silently call `get_market_data(codes=["000001.SZ"])` or `get_market_data(codes=["000001.SH"])`.

### Chinese Names

`贵州茅台` is commonly understood as `600519.SH`, but the MVP policy should still be conservative:

* Chinese-name resolution should be auditable.
* The system should know whether the mapping came from `search_symbol`, a future security master, or the LLM's own guess.
* Until that policy exists, Chinese names should trigger clarification before market-data provider calls.

This matters more for multi-listing names, abbreviations, brands, ETFs, concepts, sector names, and company names that are shared by multiple securities.

### HK / US / A-share Bare Symbols

Some bare symbols are relatively safe:

| Input | Expected normalized symbol |
| -- | -- |
| `600519` | `600519.SH` |
| `300750` | `300750.SZ` |
| `510300` | `510300.SH` |
| `159915` | `159915.SZ` |
| `QQQ` | `QQQ.US` |
| `SPY` | `SPY.US` |
| `00700` | `00700.HK` |
| `9988` | `09988.HK` |

These may be allowed, but the system should still keep an audit record:

* `raw_input`
* `normalized_symbol`
* mapping source
* warnings, if any

### LLM Pre-normalization

The LLM can decide to call tools with already-standardized symbols:

```text
User prompt: 请分析 000001 今天的行情表现
Tool call: get_market_data(codes=["000001.SZ"])
```

At that point, a normalizer inside `get_market_data` sees only `000001.SZ`. It cannot reliably know that the user originally typed ambiguous `000001`.

## 3. Desired Behavior

Design goals:

1. Preserve `original_user_prompt` for the full Agent run.
2. Check tool name and tool args before execution.
3. If the prompt contains an ambiguous raw symbol such as `000001` and the tool args use `000001.SZ` or `000001.SH`, do not silently execute. Return `Symbol Clarification Required`.
4. If the prompt contains a Chinese name and the tool args use a ticker, the MVP should require clarification unless there is an audited symbol-resolution policy.
5. Safe bare codes such as `600519`, `QQQ`, and `00700` may be allowed, but the result must record `raw_input -> normalized_symbol`.
6. Explicit user inputs such as `600519.SH`, `QQQ.US`, and `00700.HK` should not be blocked when the tool args match.
7. Explicit `000001.SZ` or `000001.SH` should not be blocked, although an optional warning can still be recorded.

## 4. Current Code Path Findings

Read-only investigation found this Web UI path:

```text
Web UI
  -> POST /sessions/{session_id}/messages
  -> SessionService.send_message()
  -> SessionService._run_attempt()
  -> SessionService._run_with_agent()
  -> AgentLoop.run(user_message=attempt.prompt, history=...)
  -> ChatLLM.stream_chat(...)
  -> response.tool_calls
  -> AgentLoop._process_tool_calls(...)
  -> AgentLoop._execute_single(...) or _execute_parallel(...)
  -> AgentLoop._invoke_tool(...)
  -> ToolRegistry.execute(...)
  -> BaseTool.execute(...)
```

Important observations:

| Question | Finding |
| -- | -- |
| Is original prompt available before tool execution? | Yes. `AgentLoop.run(user_message=...)` receives it and writes it to `req.json` and trace. |
| Are tool name and args available before execution? | Yes. `_process_tool_calls` receives `response.tool_calls`; each tool call has `tc.name` and `tc.arguments`. |
| Is there a unified tool execution path? | Mostly yes. `_execute_single` and `_execute_parallel` both call `_invoke_tool`, and `_invoke_tool` calls `ToolRegistry.execute`. |
| Does `_invoke_tool` have original prompt today? | No. It receives only `tool_name` and `args`; a future guard would need prompt state from `AgentLoop.run`. |
| Can `search_symbol` precede `get_market_data`? | Yes. The QQQ Web UI run called `search_symbol(query="QQQ")` before `get_market_data(codes=["QQQ.US"])`. |
| Can LLM rewrite symbols without `search_symbol`? | Yes. `000001` became `000001.SZ`, and `贵州茅台` became `600519.SH`. |

## 5. Proposed Guard Architecture

Add a pre-tool guard layer before provider execution.

Recommended first location:

* `AgentLoop._process_tool_calls` or immediately before `_execute_single` / `_execute_parallel` launch a tool call.
* The guard should run before `trace.write({"type": "tool_call", ...})` records an executed call, or it should record a separate `symbol_guard` event followed by a synthetic tool result.

Inputs:

* `original_user_prompt`
* `tool_name`
* `tool_args`
* optional recent `search_symbol` results from the same run

Output:

```python
{
    "decision": "allow" | "block" | "clarify",
    "reason": "...",
    "matched_rule": "...",
    "warnings": [...],
    "raw_input_candidates": [...],
    "tool_symbol": "...",
    "normalized_symbol": "...",
    "source": "explicit" | "normalizer" | "search_symbol" | "llm_unverified"
}
```

Suggested pure function:

```python
evaluate_symbol_intent_guard(
    original_prompt: str,
    tool_name: str,
    tool_args: dict,
    recent_symbol_search_results: list | None = None,
) -> dict
```

The function should be pure and testable. It should not call data providers, LLMs, or network APIs.

## 6. Guard Rules MVP

### Rule A: Explicit Symbol In Prompt

If the prompt explicitly contains `600519.SH`, `QQQ.US`, `00700.HK`, `000001.SZ`, or `000001.SH`, and the tool args match that explicit symbol:

* Decision: `allow`
* Source: `explicit`

If the prompt contains an explicit symbol but the tool calls a different symbol:

* Decision: `block`
* Reason: `tool_symbol_mismatch`

### Rule B: Safe Bare Symbols

If the prompt contains a safe bare symbol and the tool arg matches the normalizer's unique mapping:

| Prompt token | Allowed tool symbol |
| -- | -- |
| `600519` | `600519.SH` |
| `300750` | `300750.SZ` |
| `510300` | `510300.SH` |
| `159915` | `159915.SZ` |
| `QQQ` | `QQQ.US` |
| `SPY` | `SPY.US` |
| `00700` | `00700.HK` |
| `9988` | `09988.HK` |

Decision:

* `allow`
* Record `raw_input`, `normalized_symbol`, `matched_rule`, and any warning.

### Rule C: Ambiguous 000001

If the prompt contains `000001` without an explicit suffix or disambiguating words such as `平安银行`, `上证指数`, `SZ`, `SH`, `深市`, or `沪市`:

* Decision: `clarify`
* Do not call provider.

This applies even if the tool arg is already `000001.SZ` or `000001.SH`.

### Rule D: Chinese Names

If the prompt contains Chinese company/security names and the tool arg is a ticker:

MVP decision:

* `clarify`
* Do not call provider unless a future audited `search_symbol` policy is enabled.

Future relaxed policy may allow:

* `search_symbol` was called in the same run.
* The search query exactly matches the Chinese name.
* The top candidate exactly matches the tool symbol.
* Candidate count and confidence meet a documented threshold.
* The mapping is recorded in metadata.

### Rule E: Tool Arg Not Traceable To Prompt

If a tool symbol does not appear in the prompt, is not a normalizer-explainable mapping, and is not backed by an audited `search_symbol` result:

* MVP decision: `block` for `get_market_data`.
* Alternative later policy: allow with warning for non-time-sensitive, exploratory prompts.

## 7. Clarification Response

When the guard returns `clarify`, the tool should not call the provider. It should return a synthetic tool result that the Agent can surface to the user.

Suggested response:

```markdown
# Symbol Clarification Required

我检测到你的标的输入存在歧义，不能静默选择一个证券继续分析。

- 原始输入：000001
- 可能含义：
  - 000001.SZ 平安银行
  - 000001.SH 上证指数

请明确你要分析哪一个。
```

Suggested JSON envelope:

```json
{
  "status": "blocked",
  "error_code": "symbol_clarification_required",
  "message": "Symbol Clarification Required",
  "raw_input": "000001",
  "candidate_symbols": ["000001.SZ", "000001.SH"],
  "decision": "clarify"
}
```

## 8. Metadata and Trace

Every guard decision should be auditable.

Record fields:

| Field | Meaning |
| -- | -- |
| `original_prompt_excerpt` | Redacted short excerpt of the user prompt. |
| `tool_name` | Tool being called. |
| `tool_symbol` | Symbol in tool args. |
| `raw_symbol_candidates` | Raw prompt tokens or names that may refer to the tool symbol. |
| `decision` | `allow`, `block`, or `clarify`. |
| `reason` | Human-readable explanation. |
| `warnings` | Guard warnings. |
| `matched_rule` | Rule A/B/C/D/E. |
| `source` | `explicit`, `normalizer`, `search_symbol`, or `llm_unverified`. |

If `allow`, still record:

* `raw_input`
* `normalized_symbol`
* `source`
* warnings

Trace event suggestion:

```json
{
  "type": "symbol_intent_guard",
  "iter": 3,
  "tool": "get_market_data",
  "decision": "clarify",
  "matched_rule": "C",
  "tool_symbol": "000001.SZ",
  "raw_symbol_candidates": ["000001"]
}
```

## 9. Feature Flag

Recommended flag:

```text
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Rules:

* Initial MVP default: off. Current default policy is documented in "Default Policy Update: 2026-07-08" below.
* First integration: only `get_market_data`.
* Do not affect provider chains.
* Do not affect Web UI code.
* Do not change `search_symbol` behavior in the MVP.
* After validation, consider `get_stock_news`, `get_fund_flow`, and `get_research_reports`.

## 10. Implementation Phases

### Phase A: Design Only

Current phase.

Deliverables:

* Design document.
* Code-path investigation.
* Backlog and roadmap updates.

### Phase B: Pure Guard Function + Tests

Implement only:

```python
evaluate_symbol_intent_guard(...)
```

No AgentLoop integration.

Tests should cover:

* explicit symbol allow
* safe bare symbol allow
* `000001` clarification
* Chinese-name clarification
* wrong tool-symbol block
* no-symbol prompt with tool-symbol block/warning

### Phase C: Feature-flagged AgentLoop Integration

Integrate only when:

```text
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

MVP scope:

* Only `get_market_data`.
* If blocked or clarify, append a synthetic tool result and do not call provider.
* Record trace metadata.

### Phase D: Web UI Retest

Retest:

* `600519`
* `QQQ`
* `00700`
* `000001`
* `贵州茅台`

Expected:

* safe bare symbols work
* ambiguous `000001` asks clarification
* Chinese names ask clarification in MVP
* `_data_quality` remains intact for allowed calls

### Phase E: Expand To Other Tools

Only after Phase D passes:

* `get_stock_news`
* `get_fund_flow`
* `get_research_reports`
* A-share specialty tools

## 11. Acceptance Tests

| # | Prompt | Tool symbol | Expected decision |
| -- | -- | -- | -- |
| 1 | `请分析 600519` | `600519.SH` | allow |
| 2 | `请分析 QQQ` | `QQQ.US` | allow |
| 3 | `请分析 00700` | `00700.HK` | allow |
| 4 | `请分析 000001` | `000001.SZ` | clarify/block |
| 5 | `请分析 000001` | `000001.SH` | clarify/block |
| 6 | `请分析 000001.SZ` | `000001.SZ` | allow |
| 7 | `请分析 000001.SH` | `000001.SH` | allow |
| 8 | `请分析 平安银行` | `000001.SZ` | clarify unless audited search policy exists |
| 9 | `请分析 贵州茅台` | `600519.SH` | clarify in MVP |
| 10 | `请分析苹果公司` | `AAPL.US` | clarify in MVP |
| 11 | `请分析 600519.SH` | `300750.SZ` | block |
| 12 | `请分析今天市场` | `600519.SH` | warning/block depending on final policy |

## 12. Priority Decision

Do not enable Symbol Normalizer by default until pre-tool symbol intent guard is designed and tested.

中文：

在 pre-tool symbol intent guard 设计和测试完成前，不应默认开启 Symbol Normalizer。

`a-stock-data` should remain deferred. The project should first make symbol identity auditable and safe, then add new data sources.

## 13. Phase B Pure Function Implementation

Date: 2026-07-08.

Implemented:

* `agent/src/symbols/intent_guard.py`
* `evaluate_symbol_intent_guard(...)`
* `agent/tests/test_symbol_intent_guard.py`

Scope:

* Pure function only.
* No AgentLoop integration.
* No tool execution changes.
* No provider-chain changes.
* No Web UI changes.
* No network, LLM, or file I/O.

Current behavior:

| Scenario | Decision |
| -- | -- |
| Explicit symbol match | `allow` |
| Safe bare symbol mapping | `allow` with audit warning |
| Bare `000001` mapped to `000001.SZ` or `000001.SH` | `clarify` |
| Chinese-name prompt mapped to ticker | `clarify` |
| Explicit symbol mismatch | `block` |
| Untraceable tool symbol | `block` |
| Non-`get_market_data` tool | `allow`, reason `unsupported_tool_for_mvp` |
| Multiple symbols | highest-risk detail decides overall decision |

Next phase:

* Feature-flagged AgentLoop integration for `get_market_data` only.
* Use `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1`.
* Keep the flag off by default.

## 14. Phase C Feature-flagged AgentLoop Integration

Date: 2026-07-08.

Implemented:

* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`
* `is_pre_tool_symbol_guard_enabled()`
* AgentLoop pre-tool guard check before `get_market_data` provider execution
* Synthetic tool result for `clarify` / `block`

Scope:

* Feature flag default is off.
* Only `get_market_data` is covered.
* Flag-off behavior preserves the existing execution path.
* `clarify` / `block` does not call `_invoke_tool`, `ToolRegistry.execute`, loaders, or provider chains.
* Non-`get_market_data` tools are not intercepted.

Synthetic result shape includes:

* `ok: false`
* `status: error`
* `blocked_by: pre_tool_symbol_intent_guard`
* `decision`
* `message`
* `reason`
* `matched_rule`
* `_symbol_intent_guard`

Validation:

* Unit tests confirm flag-off zero-intercept behavior.
* Unit tests confirm flag-on allow / clarify / block behavior.
* Lightweight direct validation confirmed provider-call count is `0` for `000001` and `贵州茅台` when the flag is on.

Not done yet:

* Default-enable decision.
* Expansion to `get_stock_news`, `get_fund_flow`, or other tools.

## 15. Phase D Web UI Retest

Date: 2026-07-08.

Flags enabled for the local retest:

```text
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Result: partial pass.

What passed:

* The guard is active in the real Web UI AgentLoop path.
* Safe bare symbols were not falsely blocked:
  * `600519` reached `get_market_data` as `600519.SH`.
  * `QQQ` reached `get_market_data` as `QQQ.US`.
  * `00700` reached `get_market_data` as `00700.HK`.
* Explicit `600519.SH` was not falsely blocked.
* Ambiguous `000001` produced `blocked_by=pre_tool_symbol_intent_guard` for `get_market_data`.
* Chinese-name `贵州茅台` produced `blocked_by=pre_tool_symbol_intent_guard` for `get_market_data`.
* Final answers for `000001` and `贵州茅台` asked for clarification or confirmation.

What did not fully pass:

* `000001` still triggered non-market-data stock tools with `000001.SZ`:
  * `get_fund_flow`
  * `get_stock_news`
  * `get_sector_info`
* `贵州茅台` still triggered non-market-data stock tools with `600519.SH`:
  * `get_stock_news`
  * `get_sector_info`

Conclusion:

The current MVP protects `get_market_data`, but it is not yet a full stock-symbol intent guard. It should remain disabled by default until ambiguous or name-based symbol intent can block all stock-specific provider tools before user confirmation.

Recommended next implementation:

* Keep `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=0` by default.
* Keep `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=0` by default.
* Extend guard coverage to stock-specific tools, or introduce a per-run symbol intent state that blocks all stock-specific provider tools once clarification is required.
* Retest the Web UI after that extension.

## 16. Phase E Stock-specific Tool Guard MVP

Date: 2026-07-08.

Implemented:

* Expanded the guarded stock-specific tool list to:
  * `get_market_data`
  * `get_fund_flow`
  * `get_stock_news`
  * `get_research_reports`
  * `get_sector_info`
* Kept the same feature flag:
  * `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`
* Kept the feature flag off by default.
* Reused the same synthetic guard result shape for `clarify` and `block`.

Not covered:

* `web_search`
* `read_url`
* `search_symbol`
* `read_document`
* broad market tools
* trading tools
* non-stock tools

Symbol fields handled:

* `codes`
* `symbols`
* `symbol`
* `ticker`
* `code`
* `query` when it contains a recognizable standard symbol

Behavior:

* If the flag is off, existing behavior is preserved.
* If the flag is on and the tool is in the stock-specific guarded list, the guard checks whether the tool symbol is traceable to the original user prompt.
* If the decision is `clarify` or `block`, the original provider tool is not called.
* If the tool is not in the guarded list, it is allowed with reason `unsupported_tool_for_mvp`.

Validation:

* Symbol tests passed.
* AgentLoop integration tests passed.
* Anti-hallucination regression tests passed.
* Compile check passed.
* Lightweight mock validation confirmed:
  * `get_fund_flow` + `000001.SZ` is clarified without provider call when the flag is on.
  * `get_stock_news` + `600519.SH` from `贵州茅台` is clarified without provider call when the flag is on.
  * `get_sector_info` + safe `600519.SH` is allowed.
  * `web_search` is not affected.
  * flag off keeps `get_fund_flow` behavior unchanged.

Not done:

* No Web UI retest yet after this extension.
* No default-enable decision.
* No `a-stock-data` integration.

## 17. Phase F Web UI Stock-specific Guard Retest

Date: 2026-07-08.

Flags enabled for local retest only:

```text
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Tested prompts:

* `000001`
* `贵州茅台`
* `600519`
* `600519.SH`

Result: pass for the first-batch stock-specific guard MVP.

Findings:

* `000001`:
  * `get_market_data`, `get_fund_flow`, `get_stock_news`, and `get_sector_info` all returned `clarify`.
  * No first-batch stock provider was called.
  * Final answer asked the user to choose `000001.SZ` or `000001.SH`.
* `贵州茅台`:
  * `get_market_data`, `get_fund_flow`, `get_stock_news`, and `get_sector_info` all returned `clarify`.
  * No first-batch stock provider was called.
  * Final answer asked the user to confirm `600519.SH`.
* `600519`:
  * Allowed as `600519.SH`.
  * Stock-specific tools were allowed.
  * `_data_quality` and Data Source Summary remained present.
* `600519.SH`:
  * Explicit symbol was allowed.
  * No false block.

Conclusion:

The guard now protects the first-batch stock-specific tools in the real Web UI path.

Default-enable recommendation:

* Not yet.
* Run one more boundary retest before default-enable, covering:
  * `QQQ`
  * `00700`
  * `000001.SZ`
  * `000001.SH`
## Web UI Boundary Retest Result: 2026-07-08

The stock-specific pre-tool guard was retested in the Web UI with both feature flags enabled:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1
```

Boundary prompts:

* `QQQ`
* `00700`
* `000001.SZ`
* `000001.SH`

Result:

* `QQQ` was allowed and normalized to `QQQ.US`.
* `00700` was allowed and normalized to `00700.HK`.
* `000001.SZ` was allowed as an explicit A-share stock. The final report was blocked by freshness logic because current-day market data was stale, not by symbol clarification.
* `000001.SH` was allowed as an explicit index for market data. A later `get_sector_info` call was blocked because the tool call lacked an auditable symbol.

Design implication:

The guard is working as a symbol-intent safety layer. The next issue is not basic symbol intent, but asset-type-aware tool routing, especially for index prompts such as `000001.SH`.

Default recommendation:

* `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD`: default-on after final review and Web UI retests.
* `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER`: keep feature-flagged until more asset-type and market boundary tests are complete.

## Asset-type-aware Routing Dependency

Boundary retest showed that `000001.SH` is an explicit, traceable symbol and should not be blocked by symbol intent rules. The remaining issue is different: `000001.SH` is an index, while some tools are stock-specific or require a symbol-bearing membership query.

Conclusion:

* Pre-tool Symbol Intent Guard answers: "Is this tool symbol traceable to the user's prompt?"
* Asset-type-aware Tool Routing should answer: "Is this tool suitable for this asset type?"

Before enabling the symbol guard by default, design and review asset-type-aware routing so explicit index and ETF prompts do not flow into unsuitable stock-only tools.

## Market-wide News Exemption: 2026-07-08

Issue found during Web UI retest:

* `get_stock_news(scope=global)` was blocked by Pre-tool Symbol Intent Guard because it has no single stock symbol.
* This is a false positive: broad market / global / sector news calls are market-wide requests, not missing-symbol single-security requests.

Fix:

* `get_stock_news` is allowed without a symbol when it is explicitly market-wide:
  * `scope=global|market|all|sector`
  * `mode=global|market|all|sector`
  * or a query that clearly asks for broad market / macro / sector news and contains no symbol.

Boundary:

* Symbol-specific `get_stock_news` remains guarded.
* `get_stock_news(symbol=000001.SZ)` with prompt `000001` still clarifies.
* `get_stock_news(symbol=600519.SH)` with prompt `贵州茅台` still clarifies.
* `get_stock_news(symbol=600519.SH)` with prompt `600519` still allows.

Status:

* Unit and AgentLoop integration tests added.
* Web UI retest has not been rerun after this fix.

## Default Policy Update: 2026-07-08

Decision:

`VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD` is now enabled by default.

Reason:

The guard has passed pure tests, AgentLoop single-tool tests, AgentLoop parallel-tool tests, and real Web UI retests. It prevents a high-risk投研错误: the model silently changing an ambiguous or name-only user target into a specific ticker and then calling tools against the wrong asset.

Override:

Set one of the following values to explicitly disable it for debugging:

```bash
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=0
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=false
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=no
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=off
```

Boundary:

This default-on decision does not enable Symbol Normalizer. `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` remains default off because it automatically rewrites user input.
