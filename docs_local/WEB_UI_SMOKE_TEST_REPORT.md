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
