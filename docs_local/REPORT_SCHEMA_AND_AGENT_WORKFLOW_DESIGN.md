# Report Schema and Agent Workflow Design

## 1. Purpose

This document defines the contract between the Agent research workflow and the
future Research Workspace UI.

The goal is to prevent the Agent from returning only free-form Markdown. The
Agent should assemble a structured, auditable research report object that the
UI can render consistently.

This is a design document only. It does not change AgentLoop, tools, provider
chains, or Web UI code.

## 2. Design Principles

1. **Data first, narrative second**
   * Tool data and quality metadata must be collected before AI interpretation.

2. **No unsupported capability**
   * The report must not pretend to support analyst forecasts, target prices,
     peer comparison, or valuation metrics when inputs are missing.

3. **Every conclusion has source**
   * Major conclusions should trace back to a data source, reporting period,
     or an explicitly marked model interpretation.

4. **Raw data and AI interpretation separated**
   * Raw financial statements, market values, and source metadata should not be
     mixed with the AI memo text.

5. **Report schema should be UI independent**
   * The same schema should support Web UI, CLI exports, JSON reports, and
     future PDF/Markdown exports.

## 3. Top-level Research Report Schema

Recommended top-level structure:

```json
{
  "research_meta": {},
  "symbol": {},
  "market_snapshot": {},
  "financial_health": {},
  "investment_memo": {},
  "valuation": {},
  "risks": {},
  "data_confidence": {},
  "limitations": {}
}
```

The schema is a product contract. Exact field names can evolve during
implementation, but these sections should remain stable.

## 4. `research_meta`

Purpose:

Audit the research run and make the report traceable.

Suggested shape:

```json
{
  "run_id": "",
  "generated_at": "",
  "analysis_type": "single_stock_research",
  "provider": "",
  "model": "",
  "data_sources": []
}
```

Fields:

| Field | Meaning |
| --- | --- |
| `run_id` | Agent/session/run identifier. |
| `generated_at` | Report generation timestamp. |
| `analysis_type` | Single stock, market overview, financial review, etc. |
| `provider` | LLM provider used for interpretation. |
| `model` | Model name used for interpretation. |
| `data_sources` | Summary list of providers/sources used. |

Policy:

* This section should never contain API keys or secrets.
* It should support later audit, replay, and troubleshooting.

## 5. `symbol`

Purpose:

Carry the resolved symbol contract. The report layer must not re-guess the
security.

Supported input examples:

```text
600519
贵州茅台
QQQ
00700
```

Suggested shape:

```json
{
  "input": "600519",
  "normalized_symbol": "600519.SH",
  "display_name": "贵州茅台",
  "market": "CN",
  "asset_type": "stock",
  "resolution_status": "resolved",
  "warnings": []
}
```

Resolution statuses:

| Status | Meaning |
| --- | --- |
| `resolved` | Symbol is explicit or safely normalized. |
| `needs_confirmation` | User input is ambiguous or a name without confirmed ticker. |
| `invalid` | Symbol cannot be recognized. |
| `market_wide` | User asked a market-level question, not a single-symbol question. |

Policy:

* `symbol.input` preserves the user-facing input.
* `symbol.normalized_symbol` is the internal working symbol.
* Ambiguous symbols such as `000001` should not silently become one asset.
* Chinese names should require confirmation unless a verified mapping layer is
  implemented.

## 6. `market_snapshot`

Purpose:

Represent market data from tools. LLM must not invent prices, volume, turnover,
or trend fields.

Suggested shape:

```json
{
  "status": "available",
  "price": null,
  "change": null,
  "change_pct": null,
  "volume": null,
  "turnover": null,
  "trend": {
    "summary": "",
    "period": "",
    "facts": []
  },
  "benchmark_comparison": {
    "benchmark_symbol": "",
    "benchmark_name": "",
    "relative_performance": null,
    "notes": ""
  },
  "data_quality": {}
}
```

Allowed statuses:

| Status | Meaning |
| --- | --- |
| `available` | Market data was retrieved and can be shown. |
| `partial` | Some fields are missing. |
| `missing` | No usable market data was retrieved. |
| `blocked` | Guard or policy prevented the tool call. |

Policy:

* Prices and volume must come from market data tools.
* Strong time-sensitive questions must respect Data Freshness / Report Gate.
* If data is stale, missing, or unknown, the report should disclose that before
  any interpretation.

## 7. `financial_health`

Purpose:

Represent raw financial statements and AI interpretation separately.

Supported statements:

```text
income
balance
cashflow
```

Suggested shape:

```json
{
  "status": "available",
  "statements": [
    {
      "type": "income",
      "provider": "a_stock_data",
      "source": "sina_financial_report",
      "upstream": "a-stock-data",
      "period": "annual",
      "latest_data_date": "2026-03-31",
      "metrics": {},
      "raw_rows_ref": "",
      "data_quality": {}
    }
  ],
  "summary": {
    "revenue_trend": "",
    "profit_trend": "",
    "balance_sheet_view": "",
    "cashflow_view": "",
    "facts": [],
    "interpretation": ""
  },
  "quality": {
    "reporting_period_status": "",
    "warnings": []
  }
}
```

Policy:

* `statements[]` contains raw data and source metadata.
* `summary` contains AI interpretation.
* Financial data should use reporting-period language, not intraday freshness
  language.
* `indicators` is not a first-class data source in the MVP. It belongs to
  future Metrics Engine behavior.

## 8. `investment_memo`

Purpose:

Provide the fixed Agent memo structure for user consumption.

Suggested shape:

```json
{
  "thesis": "",
  "bull_case": [],
  "bear_case": [],
  "key_risks": [],
  "monitor_items": []
}
```

Policy:

* Keep this section structured.
* Do not allow unbounded free-form essays as the only output.
* Separate data facts from model interpretation.
* No buy/sell recommendation.
* No target price.
* No invented forecast.

## 9. `valuation`

Purpose:

Reserve a structured slot for valuation while clearly stating current limits.

Current MVP status:

```text
partial
```

Suggested shape:

```json
{
  "status": "partial",
  "available_metrics": [],
  "missing_metrics": [
    "PE",
    "PB",
    "target_price"
  ],
  "missing_inputs": [
    "market_cap",
    "shares_outstanding",
    "forecast_earnings"
  ],
  "reason": "Valuation requires financial data, market data, shares or market cap, and period alignment."
}
```

Policy:

* Do not pretend PE/PB/target price is supported unless the inputs were
  retrieved and the calculation method is defined.
* Valuation should become a future Engine, not a loose paragraph.

## 10. `risks`

Purpose:

Make risk output separately renderable and auditable.

Suggested shape:

```json
{
  "business_risks": [],
  "financial_risks": [],
  "market_risks": [],
  "data_risks": [],
  "unsupported_risks": []
}
```

Policy:

* `data_risks` should include missing or stale data warnings.
* `unsupported_risks` should include topics that need external sources.
* The Agent should avoid presenting unsupported risks as sourced facts.

## 11. `data_confidence`

Purpose:

Expose what the system actually knew when producing the report.

Suggested shape:

```json
{
  "market_data": {
    "provider": "",
    "source": "",
    "date": "",
    "status": "",
    "warnings": []
  },
  "financial_data": {
    "provider": "a_stock_data",
    "source": "sina_financial_report",
    "upstream": "a-stock-data",
    "reporting_period": "",
    "period_end_date": "2026-03-31",
    "status": "",
    "warnings": []
  },
  "news_data": {
    "provider": "",
    "source": "",
    "latest_timestamp": "",
    "status": "",
    "warnings": []
  },
  "warnings": []
}
```

Policy:

* This section should be visible in UI, not hidden in logs.
* It should include provider/source/date/period/status for each data class.
* Fallback use should be disclosed.
* Primary provider failure should be disclosed.

## 12. `limitations`

Purpose:

Make unsupported capabilities explicit.

Suggested shape:

```json
{
  "unsupported": [
    "analyst_forecast",
    "target_price",
    "peer_comparison",
    "earnings_call"
  ],
  "notes": []
}
```

Current unsupported items:

* Analyst forecast.
* Target price.
* Peer comparison.
* Earnings call / transcript analysis.
* Automatic buy/sell decision.
* AI stock picking.
* Unsupported valuation metrics.

## 13. Agent Research Workflow v1

Workflow:

```text
User Input
    -> Symbol Resolution
    -> Asset Classification
    -> Research Plan Generation
    -> Tool Execution
    -> Data Validation
    -> Report Assembly
    -> AI Interpretation
    -> Structured Report
```

## 14. Step 1: Symbol Resolution

Responsible for:

* Ticker recognition.
* Chinese name handling.
* Market suffix handling.
* Ambiguity detection.

Output:

```json
{
  "input": "",
  "normalized_symbol": "",
  "market": "",
  "asset_type": "",
  "resolution_status": "",
  "warnings": []
}
```

Policy:

* The report layer must consume this contract rather than guessing symbols.
* Ambiguous input should stop or ask for confirmation.

## 15. Step 2: Asset Classification

Responsible for classifying:

* stock
* ETF
* index
* fund
* market-wide request

Impact:

* Controls tool routing.
* Prevents ETF/index from being treated as companies.
* Prevents company financial statements from being applied to benchmarks.

## 16. Step 3: Research Plan Generation

Responsible for deciding which sections are needed:

* Market Snapshot.
* Financial Health.
* News / risks.
* Data Confidence.
* Valuation placeholder.

Policy:

* The Agent should not randomly call tools.
* The plan should be derived from the user question and capability contract.
* If the user asks for unsupported output, the plan should include a limitation
  instead of silently fabricating it.

Example plan:

```json
{
  "need_market_snapshot": true,
  "need_financial_statements": true,
  "need_news": false,
  "need_valuation": false,
  "unsupported_requests": []
}
```

## 17. Step 4: Tool Execution

All tool calls must pass through:

```text
Symbol Guard
Asset Routing Guard
Benchmark Policy
```

Policy:

* Stock-specific tools require a resolved stock symbol.
* Company financial tools should not run on ETF/index symbols.
* Benchmark Policy should only apply to auditable market-wide benchmark
  universes.
* Tool results must include provider/source/date or explain why they cannot.

## 18. Step 5: Data Validation

Every data source result should have:

* provider
* source
* date or reporting period
* quality status
* warnings

Validation examples:

| Data class | Required time field |
| --- | --- |
| Market data | trading date or timestamp |
| Financial statements | reporting period / period end date |
| News | publish timestamp |

Policy:

* Missing quality metadata is itself a warning.
* Strong time-sensitive prompts should be blocked or downgraded when market
  data is stale/missing/unknown.
* Financial statements should use reporting-period status rather than market
  freshness language.

## 19. Step 6: Report Assembly

Responsible for assembling structured fields:

```text
tool results
    -> raw section objects
    -> data confidence
    -> limitations
```

Policy:

* Raw tool data goes into structured sections.
* Data Confidence is assembled before AI interpretation.
* Missing data should produce structured empty/partial states, not prose-only
  excuses.

## 20. Step 7: AI Interpretation

Responsible for producing:

* thesis
* bull case
* bear case
* risks
* monitor items

Policy:

* AI interpretation must cite or reference available structured data.
* Unsupported claims should be marked as limitations.
* The Agent should not fill missing schema fields by guessing.
* No buy/sell recommendation.
* No target price.

## 21. Step 8: Structured Report

Final output should include:

* JSON-like structured report object for UI.
* Optional Markdown rendering for human reading.

Policy:

* UI should rely on schema fields.
* Markdown should be treated as a presentation, not the source of truth.
* The same report object should support future export.

## 22. MVP Acceptance Criteria

Input:

```text
600519
```

Required output:

* Symbol section.
* Market Snapshot section.
* Income statement.
* Balance sheet.
* Cash-flow statement.
* AI memo.
* Risks.
* Data Confidence.

Not required:

* Automatic buy/sell decision.
* Recommendation score.
* Target price.
* Forecast return.
* Peer comparison.
* Full valuation model.

Acceptance:

* If `600519` cannot be safely normalized, system asks for confirmation.
* If it resolves to `600519.SH`, company financial tools are allowed.
* Primary provider failure and fallback use are visible.
* Financial reporting period is visible.
* Missing valuation metrics are disclosed as missing.
* Report does not fabricate unsupported capability.

## 23. Implementation Recommendation

Next implementation should still be design-first:

```text
Report Schema Contract
    -> Agent Workflow Contract
    -> Minimal schema-producing harness
    -> API endpoint or CLI proof
    -> Web UI prototype
```

Do not start with UI components before the schema-producing workflow is clear.

## 24. Open Questions

1. Should schema generation be done inside AgentLoop, a post-processor, or a
   separate workflow orchestrator?
2. Should the first schema-producing proof use CLI before Web UI?
3. Should schema validation use Pydantic models later?
4. Should Markdown be generated from schema, or should schema be extracted from
   Markdown?
5. How should partial reports be represented when a section fails?
6. Should `symbol.name` be user-confirmed before Chinese-name workflows?
7. Should market-wide reports use a separate schema variant?
