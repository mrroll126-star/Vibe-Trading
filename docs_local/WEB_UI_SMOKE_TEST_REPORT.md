# Web UI Smoke Test Report

Date: 2026-07-05.

Scope: product-style Web UI smoke test on localhost only.

This report records whether Vibe-Trading can be used as a real local research product after Phase 0 setup. It does not evaluate investment quality, and it is not investment advice.

## 1. Environment

| Item | Result |
| -- | -- |
| Repository | `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading` |
| Branch | `feature/bootstrap-local-setup` |
| Backend | `127.0.0.1:8899` |
| Frontend | `127.0.0.1:5899` |
| LLM provider | `deepseek` |
| Model | `deepseek-v4-pro` |
| API auth | `API_AUTH_KEY` configured in ignored `agent/.env` |
| Shell tools | disabled, `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` |
| Remote exposure | none; localhost only |

Backend command:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

## 2. Page Smoke Test

| Page | URL | Result | Notes |
| -- | -- | -- | -- |
| Home | `http://127.0.0.1:5899/` | Passed | Web UI loaded; Chinese navigation visible. |
| Settings | `/settings` | Passed | LLM settings loaded after refresh; provider showed `deepseek`; key displayed only as configured, not exposed. |
| Agent | `/agent` | Passed | Prompt box worked; research tasks could be submitted. |
| Runtime | `/runtime` | Passed | Read-only runtime status loaded; broker connectors were not authorized and not started. |
| Reports | `/reports` | Partial | Page opened but remained on `Loading...` during this smoke test. |
| Session history | Agent sidebar | Passed | Web UI showed the SPY.US and 600519.SH sessions in the session list. |

## 3. Web Research Task: SPY.US

Prompt:

```text
请生成 SPY.US 的简短市场概览，包括近期趋势、主要风险和后续关注点。不要给买卖建议。
```

Result:

| Check | Result |
| -- | -- |
| Web session | `884ecc8115d1` |
| Run ID | `20260705_164326_08_79a439` |
| Status | success |
| Runtime shown in UI | completed, 11 steps, about 34 seconds |
| Report visible in Web UI | yes |
| No-investment-advice wording | present |
| Shell tools | not enabled |

Tool and trace summary:

* Session trace ended with success.
* Tool calls included `get_market_data`, `get_stock_profile`, `web_search`, and `read_url`.
* Local run details were available through `/runs/20260705_164326_08_79a439`.
* LLM usage file recorded 6 DeepSeek calls and 212,174 total provider-reported tokens.

Report summary:

* The output described SPY.US recent trend, macro and sector risks, and follow-up points.
* It included a clear statement that the content was for research reference only and was not buy/sell advice.

## 4. Web Research Task: 600519.SH

Prompt:

```text
请生成 600519.SH 的简短研究摘要，包括近期走势、主要风险和后续关注点。不要给买卖建议。
```

Result:

| Check | Result |
| -- | -- |
| Web session | `bd1bbb81c6fc` |
| Run ID | `20260705_164700_99_303723` |
| Detailed run endpoint | success |
| Web session trace | success |
| Report visible in Web UI | yes |
| No-investment-advice wording | present |
| Shell tools | not enabled |

Tool and trace summary:

* Session trace ended with success.
* Tool calls included A-share oriented tools such as `get_market_data`, `get_financial_statements`, `get_stock_news`, `get_research_reports`, `get_fund_flow`, `get_margin_trading`, `get_shareholder_count`, `get_northbound_flow`, `get_sector_info`, `get_block_trades`, and `get_lockup_expiry`.
* One `read_url` call returned an HTTP 451 style remote-reader block for a Tencent News URL, but the overall task still completed.
* Backend logs also showed one fund-flow connection interruption and a Yahoo profile SSL failure; the task recovered and still produced a report.
* LLM usage file recorded 13 DeepSeek calls and 463,577 total provider-reported tokens.

Report summary:

* The output generated a Chinese research summary for 贵州茅台, including recent price behavior, valuation/profitability notes, major risks, and follow-up points.
* It explicitly stated that the content was not buy/sell advice.

Product note:

* The `/runs` list endpoint displayed this run with status `unknown`, while `/runs/20260705_164700_99_303723`, the Web session messages, and the Web session trace showed success. This should be treated as a product-status consistency issue to investigate later.

## 5. Findings

What worked:

* Local Web UI can start a real research task.
* DeepSeek can drive the native Agent workflow.
* Web session history is usable for recent task recall.
* A-share symbol `600519.SH` can trigger A-share oriented tools without integrating `a-stock-data`.
* Runtime page is read-only and did not start broker connectors.
* API keys were not shown in the UI or logs inspected for this report.

What needs follow-up:

* Reports page stayed on `Loading...` during this smoke test.
* Run-list status can disagree with detailed run status for the A-share task.
* There is no obvious Web UI trace viewer in the quick smoke test; trace files exist locally under ignored `agent/sessions/`.
* There was no obvious export/copy button found during the quick UI check.
* yfinance TLS remains unresolved and should not be treated as fixed by these Web task successes.
* Yahoo profile-style lookups can still hit SSL failures even when the main Agent task succeeds through other tools.

## 6. Security Check

* No real key was printed.
* `agent/.env` was not committed.
* `agent/runs/` and `agent/sessions/` were not committed.
* Services were bound only to `127.0.0.1`.
* Shell tools remained disabled.
* No provider chain was changed.
* No `a-stock-data` integration was attempted.
* No trading execution was tested.

## 7. Recommendation

The Web UI is usable enough for Phase 0 closeout, but before treating it as a daily research product, Phase 1 should first validate data-source behavior and symbol conventions.

Recommended next product validation order:

1. Run full US data-source smoke test with explicit `.US` symbols.
2. Run an A-share trading-day validation plan using `600519.SH` and one additional liquid A-share symbol.
3. Design symbol normalization before adding or changing any provider.

## 8. CLI A-Share Preflight Follow-Up

Date: 2026-07-05.

After the Web UI smoke test, two lightweight CLI research tasks were run to prepare for the next trading day:

| Symbol | Run ID | Result | Notes |
| -- | -- | -- | -- |
| `600519.SH` | `20260705_170327_44_d10190` | success | Output separated facts and inference and avoided buy/sell advice. |
| `300750.SZ` | `20260705_170559_16_fc55fe` | success | Output separated facts and inference and avoided buy/sell advice. |

This follow-up was not a Web UI test. It was run through CLI to reduce UI overhead and confirm that the original Agent workflow can handle two A-share names before a real trading-day trial.

## 9. Web UI Red-Light Prompt Retest After Guardrail MVP

Date: 2026-07-07 17:32 local time.

Prompt:

```text
请分析 600519.SH 今天盘中表现，包括最新价、涨跌幅、成交额和主要风险。只使用你实际获取到的数据；如果没有拿到当天数据，请明确说没有拿到，不要估算。
```

Run record:

| Field | Result |
| -- | -- |
| Web session | `57a481605851` |
| Run ID | `20260707_173205_10_7f61dd` |
| Status | success |
| Data Insufficient Report | No, because `get_market_data` returned fresh current-day data. |
| Data Source Summary | Present |
| Missing Data | Present |
| Source Warnings | Present |
| No Estimate Warning | Present |
| Shell tools | Disabled |
| Public exposure | No, services were bound to `127.0.0.1`. |

Data Source Summary coverage:

| Tool | Status | Date | Source | Notes |
| -- | -- | -- | -- | -- |
| `get_market_data` | fresh | 2026-07-07 | tencent | Current-day daily close warning appeared: not official close. |
| `get_fund_flow` | fresh | 2026-07-07 | eastmoney | Fund-flow metadata appeared in final report. |
| `get_stock_news` | stale | 2026-06-29 | eastmoney | Stale-news warning appeared. |
| `get_research_reports` | not called | n/a | n/a | Correctly not shown; the Source Summary does not invent statuses for uncalled tools. |

Tool calls observed in trace:

* `get_market_data`
* `get_fund_flow`
* `get_stock_news`
* `get_margin_trading`
* `get_sector_info`

Guardrail result:

* The Web UI final report included `## Data Source Summary`.
* The Web UI final report included `## Missing Data` because stock news was stale.
* The Web UI final report included `## Source Warnings` for current-day daily close and stale news.
* The Web UI final report included `## No Estimate Warning`.
* The report body still contained estimated or approximate market-fact phrasing, including estimated turnover and approximate percent-style statements.
* MVP behavior is therefore working as designed: warning is appended, but the body is not rewritten yet.

## 10. Web UI Pre-tool Symbol Guard Retest

Date: 2026-07-08 10:06-10:09 local time.

Scope: real Web UI retest with both symbol feature flags enabled for this local run only.

Backend command:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Security status:

* Services were bound only to `127.0.0.1`.
* Shell tools remained disabled.
* No remote access was exposed.
* `agent/.env`, `agent/runs/`, and `agent/sessions/` were not committed.

### 10.1 Retest Summary

| Case | Session | Run ID | Result | Tool behavior |
| -- | -- | -- | -- | -- |
| `600519` | `66a8cff0a5b7` | `20260708_100611_10_dc3c41` | Completed with `Data Insufficient Report` | Allowed; `get_market_data` called `600519.SH`; `_symbol_normalization` and `_data_quality` present. |
| `QQQ` | `541e9b698014` | `20260708_100748_61_145e43` | Completed normal report | Allowed; `get_market_data` called `QQQ.US`; `_symbol_normalization` and `_data_quality` present. |
| `00700` | `4f38726ed856` | `20260708_100758_62_0f00eb` | Completed normal report | Allowed; `get_market_data` called `00700.HK`; `_symbol_normalization` and `_data_quality` present. |
| `000001` | `634e6290c0ab` | `20260708_100809_64_c7f4c7` | Asked user to clarify `000001.SZ` vs `000001.SH` | `get_market_data` was blocked by `pre_tool_symbol_intent_guard`, but other tools still ran with `000001.SZ`. |
| `贵州茅台` | `036be2933e75` | `20260708_100820_64_0082d9` | Asked user to confirm `600519.SH` | `get_market_data` was blocked by `pre_tool_symbol_intent_guard`, but other tools still ran with `600519.SH`. |
| `600519.SH` | `ce1ed7471c1c` | `20260708_100832_19_f3a59b` | Completed with `Data Insufficient Report` | Explicit symbol was allowed; no false block. |

### 10.2 Detailed Findings

`600519`:

* `get_market_data` was called with `600519.SH`.
* `_symbol_normalization` recorded `600519.SH -> 600519.SH` because the Agent already converted the bare code before tool execution.
* `_data_quality` showed `freshness_status=stale`, `latest_data_date=2026-07-07`, `provider=tencent`.
* Final report was blocked by the time-sensitive report gate because the user asked about today and the latest market data was stale.

`QQQ`:

* `search_symbol` found `QQQ.US`.
* `get_market_data` was called with `QQQ.US`.
* `_data_quality` showed `freshness_status=stale`, `latest_data_date=2026-07-07`, `provider=yahoo`.
* `get_stock_profile` still hit the known Yahoo TLS/profile failure, but the task completed through market data and news.

`00700`:

* `get_market_data` was called with `00700.HK`.
* `_data_quality` showed `freshness_status=fresh`, `latest_data_date=2026-07-08`, `provider=yahoo`.
* Source warning appeared for current-day daily-bar close: it may represent intraday last price, not official close.
* The Agent also used web/read-url tools and attempted some unsupported HK research-report paths; this should be treated as a product-routing improvement candidate, not a symbol guard failure.

`000001`:

* `get_market_data` was blocked with `blocked_by=pre_tool_symbol_intent_guard`.
* Guard reason: `ambiguous_000001_requires_confirmation`.
* Final answer asked whether the user meant `000001.SZ` Ping An Bank or `000001.SH` Shanghai Composite.
* Gap: non-market-data tools still ran with `000001.SZ`, including `get_fund_flow`, `get_stock_news`, and `get_sector_info`.

`贵州茅台`:

* `get_market_data` was blocked with `blocked_by=pre_tool_symbol_intent_guard`.
* Guard reason: `chinese_name_requires_confirmation`.
* Final answer asked the user to confirm `600519.SH`.
* Gap: non-market-data tools still ran with `600519.SH`, including `get_stock_news` and `get_sector_info`.

`600519.SH`:

* Explicit symbol was allowed.
* `get_market_data` returned `600519.SH` data with `_symbol_normalization` and `_data_quality`.
* Final report was blocked by freshness gate because latest market data was `2026-07-07`, older than request date `2026-07-08`.

### 10.3 Overall Judgment

The Web UI retest is a partial pass:

* Pass: feature flags are honored in the real Web UI path.
* Pass: safe symbols are not incorrectly blocked.
* Pass: explicit symbols are not incorrectly blocked.
* Pass: `get_market_data` is protected against ambiguous `000001` and Chinese-name pre-normalization.
* Gap: ambiguous/name-based prompts can still trigger non-market-data tools before user confirmation.

Recommendation:

* Do not default-enable the flags yet.
* Next implementation should extend pre-tool symbol intent guard coverage to the other stock-specific tools, or apply the guard once per run before any stock-specific provider tool is allowed.

## 11. Web UI Stock-specific Symbol Guard Retest

Date: 2026-07-08 10:30-10:32 local time.

Scope: real Web UI retest after extending Pre-tool Symbol Intent Guard to the first batch of stock-specific tools.

Backend command:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Services were bound to `127.0.0.1` only. Shell tools remained disabled. The services were stopped after the test, and ports `8899` and `5899` had no listeners.

### 11.1 Retest Summary

| Case | Session | Run ID | Result |
| -- | -- | -- | -- |
| `000001` | `1a31b77c4894` | `20260708_103045_64_c24182` | Passed. All four requested stock tools were clarified and did not call providers. |
| `贵州茅台` | `ba42f63b650e` | `20260708_103113_12_894f58` | Passed. All four requested stock tools were clarified and did not call providers. |
| `600519` | `2927b3cd72ba` | `20260708_103129_14_e84c02` | Passed. Safe bare code was allowed as `600519.SH`; stock tools ran and Source Summary appeared. |
| `600519.SH` | `211a82a9a415` | `20260708_103153_15_bc8245` | Passed. Explicit symbol was allowed; no false block. |

### 11.2 Guarded Tool Results

`000001`:

| Tool | Provider called | Guard result |
| -- | -- | -- |
| `get_market_data` | No | `clarify`, `ambiguous_000001_requires_confirmation` |
| `get_fund_flow` | No | `clarify`, `ambiguous_000001_requires_confirmation` |
| `get_stock_news` | No | `clarify`, `ambiguous_000001_requires_confirmation` |
| `get_sector_info` | No | `clarify`, `ambiguous_000001_requires_confirmation` |

Final answer asked whether the user meant `000001.SZ` Ping An Bank or `000001.SH` Shanghai Composite. It did not generate a normal market, fund-flow, news, or sector analysis.

`贵州茅台`:

| Tool | Provider called | Guard result |
| -- | -- | -- |
| `get_market_data` | No | `clarify`, `chinese_name_requires_confirmation` |
| `get_fund_flow` | No | `clarify`, `chinese_name_requires_confirmation` |
| `get_stock_news` | No | `clarify`, `chinese_name_requires_confirmation` |
| `get_sector_info` | No | `clarify`, `chinese_name_requires_confirmation` |

Final answer asked the user to confirm `600519.SH` before fetching today's market, fund-flow, news, and sector data. It did not silently analyze `600519.SH`.

`600519`:

| Tool | Provider called | Result |
| -- | -- | -- |
| `get_market_data` | Yes | Allowed as `600519.SH`; `_data_quality` present; `stale`, latest `2026-07-07`, provider `tencent`. |
| `get_fund_flow` | Yes | Allowed; `_data_quality` present; `missing`, provider `eastmoney`, connection aborted. |
| `get_stock_news` | Yes | Allowed; `_data_quality` present; `fresh`, latest `2026-07-07`, provider `eastmoney`. |
| `get_sector_info` | Yes | Allowed; provider returned sector membership. |

Final report became a `Data Insufficient Report` because the user asked about today and market data was stale.

`600519.SH`:

| Tool | Provider called | Result |
| -- | -- | -- |
| `get_market_data` | Yes | Allowed; `_data_quality` present; `stale`, latest `2026-07-07`, provider `tencent`. |
| `get_fund_flow` | Yes | Allowed; `_data_quality` present; `missing`, provider `eastmoney`, connection aborted. |
| `get_stock_news` | Yes | Allowed; `_data_quality` present; `fresh`, latest `2026-07-07`, provider `eastmoney`. |
| `get_sector_info` | Yes | Allowed; provider returned sector membership. |

Final report became a `Data Insufficient Report` because the user asked about today and market data was stale.

### 11.3 Overall Judgment

This Web UI retest passed for the stock-specific guard MVP:

* `000001` no longer reaches the first-batch stock-specific providers before clarification.
* `贵州茅台` no longer reaches the first-batch stock-specific providers before confirmation.
* Safe bare code `600519` is allowed.
* Explicit symbol `600519.SH` is allowed.
* `_data_quality` and `Data Source Summary` still appear on allowed runs.

Recommendation:

* Do not default-enable the feature flags yet.
* Before default-enable, run one more boundary set covering `QQQ`, `00700`, `000001.SZ`, and `000001.SH`.
* Keep `a-stock-data` deferred until symbol intent and freshness guardrails remain stable through that boundary retest.

Product conclusion:

* The Phase 1 anti-hallucination MVP is active in the real Web UI final report path.
* Next hardening option: upgrade No Estimate Guard from warning-only to a stricter rewrite/block mode for prompts that explicitly say no estimates.
* Next feature option, if warning-only behavior is acceptable for now: proceed to feature-flagged Symbol Normalizer integration for `get_market_data`.

## 10. Web UI Bare Symbol Retest With Symbol Normalizer Enabled

Date: 2026-07-07 17:50-17:58 local time.

Backend was started with the feature flag enabled only for this local test:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1 \
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend was started locally:

```bash
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Services were bound to `127.0.0.1`; no public or Tailscale exposure was used.

### Summary

| Input | Run ID | Result | Tool argument observed | Normalization metadata | Data quality | Key finding |
| -- | -- | -- | -- | -- | -- | -- |
| `600519` | `20260707_175004_29_e1ff41` | completed | `600519.SH` | present | fresh, 2026-07-07, tencent | Compatible path passed, but the LLM changed the bare code before the tool call. |
| `QQQ` | `20260707_175103_82_517a2b` | completed | `QQQ.US` | present | stale, 2026-07-06, yahoo | Search/LLM normalized before `get_market_data`; Source Summary disclosed stale market data. |
| `00700` | `20260707_175432_05_eb20f8` | completed | `00700.HK` | present | fresh, 2026-07-07, yahoo | Compatible path passed, but raw bare input did not reach the tool. |
| `000001` | `20260707_175623_17_caf048` | completed | `000001.SZ` | present with ambiguous warning | fresh, 2026-07-07, tencent | Boundary issue: the Agent silently chose `000001.SZ` before the tool entry guard could require confirmation. |
| `贵州茅台` | `20260707_175745_30_b963eb` | completed | `600519.SH` | present | fresh, 2026-07-07, tencent | Boundary issue: the Agent mapped the Chinese name to `600519.SH` before the normalizer could request confirmation. |

### Observed Metadata

For successful market-data calls, `_symbol_normalization` and `_data_quality` both appeared in the `get_market_data` result. This confirms that enabling the feature flag does not remove the data-quality guardrails.

Observed `_data_quality` examples:

| Input | normalized_symbol | freshness_status | latest_data_date | provider |
| -- | -- | -- | -- | -- |
| `600519` | `600519.SH` | fresh | 2026-07-07 | tencent |
| `QQQ` | `QQQ.US` | stale | 2026-07-06 | yahoo |
| `00700` | `00700.HK` | fresh | 2026-07-07 | yahoo |
| `000001` | `000001.SZ` | fresh | 2026-07-07 | tencent |
| `贵州茅台` | `600519.SH` | fresh | 2026-07-07 | tencent |

### Guardrail Findings

* `Data Source Summary` appeared in all five final reports.
* `Source Warnings` appeared where relevant.
* `No Estimate Warning` appeared in four of the five reports.
* `_data_quality` remained present after symbol normalization metadata was added.
* The Web UI path often lets the LLM or `search_symbol` convert the user's natural input before `get_market_data` sees it.

### Product Conclusion

The feature-flagged normalizer is compatible with the Web UI `get_market_data` path, but this retest does not prove that the tool-entry normalizer safely handles all raw Web UI input. In real Agent runs, the model can pre-normalize ambiguous or named symbols before tool execution.

Do not enable the Symbol Normalizer by default yet. The next design task should address pre-tool symbol intent, especially ambiguous inputs like `000001` and Chinese names like `贵州茅台`.
