# a-stock-data Live Smoke Test Plan

Date: 2026-07-09

Status: design only.

No live request was run for this document. No dependency was installed. No business code was changed.

## 1. Purpose

This test is not product integration and not a Web UI test.

Purpose:

* Verify whether the candidate `a-stock-data` financial-statement entry works from this machine.
* Observe the raw output shape before any production-style adapter is implemented.
* Confirm whether the existing `normalize_a_stock_financials_result(...)` helper can consume the raw rows.

It should not enter AgentLoop, should not modify provider chains, and should not change `get_financial_statements` runtime behavior.

中文：

这只是一次受控 smoke test 设计，用来观察原始数据形态，不是正式接入。

## 2. Preconditions

Required before running any future live smoke:

* Current branch has been pushed to the user's fork.
* `git status` is clean.
* `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER` remains default off.
* No `agent/.env` content is read or printed.
* No vendor code is copied into this repository.
* No `local_reports` output is committed.
* Only a few A-share stock symbols are tested.
* Every request has a timeout.
* Requests are serial, with a short sleep/rate limit.
* Failure is acceptable and must be recorded.

Sensitive paths that must remain untracked:

* `agent/.env`
* `agent/runs`
* `agent/sessions`
* `local_reports`

## 3. Candidate Endpoint

Readonly source:

* Repository: `https://github.com/simonlin1212/a-stock-data`
* Local readonly clone: `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/_vendor_readonly/a-stock-data`
* Observed commit: `bcda405`

Recommended candidate:

```text
sina_financial_report(code: str, report_type: str = "lrb", num: int = 8) -> list[dict]
```

Location in upstream Skill:

```text
SKILL.md, Layer 6.4: 新浪财报三表（资产负债表/利润表/现金流量表）
```

Why this candidate:

* It directly targets financial statements.
* It uses Sina Finance rather than Eastmoney.
* It is described as free and no-key.
* It only needs `requests`.
* It returns rows keyed by `报告期`, which the current normalizer already recognizes.
* It returns a simple `list[dict]`, which the current normalizer already accepts.

Parameters:

| Parameter | Meaning | Notes |
| --- | --- | --- |
| `code` | Six-digit A-share code | Upstream snippet expects `600519`, not `600519.SH` |
| `report_type` | Statement type | `lrb`, `fzb`, `llb` |
| `num` | Number of periods | Default 8 |

Statement mapping:

| Local statement_type | Upstream report_type | Meaning |
| --- | --- | --- |
| `income` | `lrb` | Income statement / 利润表 |
| `balance` | `fzb` | Balance sheet / 资产负债表 |
| `cashflow` | `llb` | Cash-flow statement / 现金流量表 |
| `indicators` | unknown | Not covered by this candidate |
| `all` | call all three separately | Design only; not needed for first smoke |

Symbol format:

* Upstream accepts pure six-digit code.
* The snippet internally chooses `sh` if code starts with `6`, otherwise `sz`.
* Project symbols such as `600519.SH` or `300750.SZ` should be converted to `600519` / `300750` in the future smoke script.

Dependencies:

* Required for this candidate: `requests`.
* Not required for this candidate: `mootdx`, `pandas`, `stockstats`.
* The broader `a-stock-data` Skill lists `mootdx requests pandas stockstats`.

Authentication:

* No token or cookie found for Sina financial statements.
* `iwencai` key is unrelated and should not be used in this smoke.

Expected raw shape:

```json
[
  {
    "报告期": "2026-03-31",
    "净利润": "...",
    "净利润_同比": "...",
    "...": "..."
  }
]
```

Underlying API shape described by upstream:

```text
result.data.report_list
```

Each report period contains:

```text
data: [{item_title, item_value, item_tongbi}]
```

Source/upstream fields:

* Raw rows do not appear to include `source` or `upstream`.
* The smoke wrapper should add:
  * `source=sina_financial_report`
  * `upstream=a-stock-data`

Unknowns:

* Whether Sina endpoint will work from this machine at test time.
* Whether all fields remain stable.
* Whether values are in yuan, ten-thousand yuan, or another unit for every item.
* Whether all A-share stocks return all three statement types.
* Whether `indicators` should later map to a different endpoint such as mootdx finance snapshot.

## 4. Test Symbols

Recommended eligible stock symbols:

* `600519.SH`
* `300750.SZ`

Reason:

* Both are explicit A-share stock symbols.
* Both are accepted by the current fallback eligibility helper.
* They avoid index / ETF ambiguity.

Negative cases:

* `000001.SH`: index, should not enter fallback live path.
* `510300.SH`: ETF, should not enter fallback live path.

Recommendation:

Do not run live requests for negative cases. The current unit tests already cover eligibility. Live smoke should focus on whether the external financial endpoint works for eligible stocks.

## 5. Execution Mode Options

### Option A: External one-off smoke script outside tool chain

Example future file:

```text
scripts/smoke_a_stock_data_financials.py
```

This script would call the candidate endpoint directly and pass the raw rows to `normalize_a_stock_financials_result(...)`.

Advantages:

* Lowest risk.
* Does not enter AgentLoop.
* Does not change `get_financial_statements`.
* Does not change provider chains.
* Can save shape summaries to ignored `local_reports`.

Disadvantages:

* Later migration into `fetch_a_stock_financials(...)` is still needed.
* It does not prove the final tool path yet.

### Option B: Implement live fetch behind stub then run direct function

Advantages:

* Closer to the future production path.

Disadvantages:

* More business code change.
* Higher chance of bringing live logic into the main tool chain too early.
* More rollback surface.

Recommendation:

Use Option A first.

## 6. Dependency Policy

For the recommended Sina financial-statement smoke:

* `requests` is needed.
* The current project environment likely already has `requests`, but this must be checked before running.
* Do not install dependencies during design.

If future smoke requires installing anything:

1. Ask user for approval first.
2. Install only into the project `.venv`.
3. Do not use `sudo`.
4. Do not modify global Python.
5. Record command and result in `docs_local/TEST_REPORT.md`.
6. Do not commit generated cache, reports, or environment files.

Do not install the broader set `mootdx pandas stockstats` unless a later endpoint truly needs them.

## 7. Smoke Script Design

Future script requirements:

* Does not enter AgentLoop.
* Does not modify `get_financial_statements`.
* Does not modify provider chains.
* Does not read `agent/.env`.
* Does not require an LLM key.
* Uses timeout 10-15 seconds.
* Makes at most one request per symbol per statement type.
* Sleeps between requests.
* Captures all exceptions.
* Outputs only a raw shape summary, not large raw payloads.
* Saves structured output to `local_reports/a_stock_data_smoke_*.json`.
* Confirms `local_reports` is ignored.
* Does not commit result files.

Recommended first statement types:

* `income` -> `lrb`
* `balance` -> `fzb`
* `cashflow` -> `llb`

First smoke can start with only:

```text
600519.SH income
300750.SZ income
```

Then extend to balance/cashflow if the income test works.

Output structure:

```json
{
  "ok": true,
  "symbol": "600519.SH",
  "statement_type": "income",
  "elapsed_sec": 1.23,
  "raw_type": "list",
  "row_count": 8,
  "sample_keys": ["报告期", "净利润"],
  "date_fields_detected": ["报告期"],
  "source_fields_detected": [],
  "normalized_ok": true,
  "normalized_freshness_status": "unknown",
  "error": null
}
```

## 8. Success Criteria

The smoke is successful if:

* At least one eligible stock returns rows.
* Rows include a date field such as `报告期`.
* The current normalizer can process the rows.
* The smoke script exits without uncaught exceptions.
* No API key, token, cookie, or `.env` content is printed.
* Any output file is saved only under ignored `local_reports`.

## 9. Failure Criteria

Failure is acceptable if it is recorded.

Failure conditions:

* `requests` is unavailable and user does not approve installing it.
* Endpoint requires token/cookie unexpectedly.
* All requests time out.
* Endpoint returns HTML, login, anti-bot, or risk-control page.
* Rows have no usable date.
* Rows are empty for all tested symbols.
* Rate limiting or connection reset prevents useful output.

## 10. Rollback

Because the recommended smoke is external and one-off:

* No business-code rollback should be needed.
* Delete the smoke script if it is temporary, or commit it only after user approval.
* Do not commit `local_reports`.
* Keep `VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER=0`.

If a committed smoke script later causes confusion:

* Revert only that script commit.
* Keep the mock-first hook and normalizer unchanged.

## 11. Next Step After Smoke

If smoke passes:

1. Implement live fetch behind `fetch_a_stock_financials(...)`.
2. Keep the feature flag default off.
3. Run direct function tests first.
4. Run CLI/tool tests second.
5. Run Web UI only after direct path is stable.

If smoke fails:

1. Keep the current fallback stub.
2. Re-check the Sina endpoint shape.
3. Consider mootdx finance snapshot for `indicators`.
4. Consider another A-share financial data source.

