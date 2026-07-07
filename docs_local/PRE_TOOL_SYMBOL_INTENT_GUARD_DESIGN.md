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

* Default: off.
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
