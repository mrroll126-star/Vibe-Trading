# LLM Provider Strategy For Investment Research

Status: design document only. No real API key has been configured, no business code has been changed, and no research task has been run.

## 1. Purpose

This project needs more than one model profile.

Investment research work includes different task types:

* Deep text reasoning over companies, industries, and macro events.
* Cheap summarization of news, transcripts, and notes.
* Chart and screenshot understanding.
* Long report reading.
* Structured JSON extraction for dashboards and workflows.
* Local fallback when cloud services are unavailable.

One model is unlikely to be best for all of these. The strategy is to start with one strong text model, prove the original Vibe-Trading workflow, and then add task routing carefully.

## 2. Providers Supported By Current Code

Source of truth: `agent/src/providers/llm_providers.json`.

| Provider name | Display name | Key Env | Base URL Env | Default model | Auth |
| -- | -- | -- | -- | -- | -- |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | `deepseek/deepseek-v4-pro` | API key |
| `openai` | OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | `gpt-5.5` | API key |
| `openai-codex` | OpenAI Codex / ChatGPT OAuth | none | `OPENAI_CODEX_BASE_URL` | `openai-codex/gpt-5.3-codex` | OAuth |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` | `deepseek-v4-pro` | API key |
| `gemini` | Gemini | `GEMINI_API_KEY` | `GEMINI_BASE_URL` | `gemini-3.5-flash` | API key |
| `groq` | Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` | `meta-llama/llama-4-maverick-17b-128e-instruct` | API key |
| `dashscope` | DashScope / Qwen | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | `qwen-plus-latest` | API key |
| `qwen` | Qwen alias | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | `qwen-plus-latest` | API key |
| `zhipu` | Zhipu | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | `glm-5.1` | API key |
| `glm` | GLM / Zhipu alias | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | `glm-5.1` | API key |
| `moonshot` | Moonshot / Kimi | `MOONSHOT_API_KEY` | `MOONSHOT_BASE_URL` | `kimi-k2.6` | API key |
| `minimax` | MiniMax | `MINIMAX_API_KEY` | `MINIMAX_BASE_URL` | `MiniMax-M3` | API key |
| `mimo` | Xiaomi MIMO | `MIMO_API_KEY` | `MIMO_BASE_URL` | `MiMo-72B-A27B` | API key |
| `zai` | Z.ai | `ZAI_API_KEY` | `ZAI_BASE_URL` | `glm-5.1` | API key |
| `ollama` | Ollama local | none | `OLLAMA_BASE_URL` | `qwen2.5:32b` | local/no key |

Important notes:

* Anthropic is not a first-class provider in current project metadata. Anthropic models may be reachable through OpenRouter, but native `ANTHROPIC_API_KEY` routing is not defined in the current provider list.
* Gemini uses `GEMINI_API_KEY`, not `GOOGLE_API_KEY`, in this project.
* Vision routing is not yet proven in this local project. Treat Qwen-VL or Kimi Vision as a design target until tested through a compatible provider/model path.

## 3. Recommended Model Combination

### Main Reasoning Model

Recommended first choice:

* Provider: `deepseek`
* Model: `deepseek-v4-pro`

Why:

* Good fit for Chinese-language investment research and text reasoning.
* Strong cost/performance candidate for daily research.
* The user's preference is to prioritize domestic models.

Alternative route:

* Provider: `openrouter`
* Model: `deepseek/deepseek-v4-pro`

Use this if OpenRouter account management is easier than managing multiple direct provider accounts.

### Low-Cost Fast Model

Recommended:

* Provider: `dashscope` or `qwen`
* Model: `qwen-plus-latest`

Use for:

* News clipping summaries.
* Short note cleanup.
* First-pass classification.
* Fast table-to-bullets transformation.

Alternative:

* Provider: `groq`
* Model: `meta-llama/llama-4-maverick-17b-128e-instruct`

Use only after confirming quality is acceptable for Chinese financial text.

### Vision / Chart Recognition Model

Design target:

* Qwen-VL through DashScope/Qwen-compatible route.
* Kimi Vision through Moonshot/Kimi-compatible route.
* Gemini vision model through Gemini-compatible route.

Current caveat:

* The project provider metadata lists text-oriented default models.
* This local project has not yet verified image upload or vision prompt handling through the Vibe-Trading agent path.
* Do not rely on DeepSeek for chart OCR or screenshot interpretation in this stage.

Use for:

* Chart screenshot interpretation.
* OCR from broker screenshots.
* Extracting tables from images.
* Visual sanity checks of dashboard screenshots.

### Long Document Reading Model

Recommended:

* Provider: `moonshot`
* Model: `kimi-k2.6`

Why:

* Kimi/Moonshot is a strong candidate for long Chinese documents and reports.
* Useful for annual reports, broker research PDFs, transcripts, and policy documents.

Alternatives:

* `zhipu` / `glm` with `glm-5.1`.
* `openrouter` routed to a long-context model.

### Structured JSON Model

Recommended:

* Provider: `deepseek`
* Model: `deepseek-v4-pro`

Fallback:

* Provider: `qwen`
* Model: `qwen-plus-latest`

Use for:

* Extracting structured fields from research notes.
* Producing dashboard-ready summaries.
* Turning research into JSON for later BI/data product workflows.

### Local Fallback Model

Recommended:

* Provider: `ollama`
* Model: `qwen2.5:32b` or another locally installed model.

Use for:

* Draft summaries.
* Offline experiments.
* Privacy-sensitive notes.
* Emergency fallback when cloud keys fail.

Limitations:

* Quality depends on local model size.
* Speed depends on local hardware.
* Tool-calling quality must be tested before relying on it for real Agent workflows.

## 4. Task Routing Strategy

This is a future design. Current code primarily uses one active `LANGCHAIN_PROVIDER` at runtime. A router should be added only after the basic single-provider research task works.

| Task type | Primary route | Fallback route | Notes |
| -- | -- | -- | -- |
| `text_reasoning` | `deepseek` / `deepseek-v4-pro` | `openrouter` DeepSeek, then `moonshot` | Main company/sector/macro analysis. |
| `cheap_summary` | `qwen` or `dashscope` / `qwen-plus-latest` | `groq`, then `ollama` | Short summaries, low-risk transformations. |
| `vision_chart_ocr` | Qwen-VL or Kimi Vision design target | Gemini vision design target | Not yet verified in current project path. |
| `long_report_reading` | `moonshot` / `kimi-k2.6` | `zhipu` / `glm-5.1`, then OpenRouter long-context model | Annual reports, broker PDFs, transcripts. |
| `structured_json` | `deepseek` / `deepseek-v4-pro` | `qwen` / `qwen-plus-latest` | Must validate strict JSON output. |
| `local_fallback` | `ollama` | none | Local-only fallback; quality varies. |

Routing rules:

1. Route by task intent, not by user-visible provider preference alone.
2. Prefer domestic models for Chinese investment research unless quality fails.
3. Keep one default provider for simple first deployment.
4. Add router only after single-provider Agent workflow is proven.
5. Router output must record which provider/model handled each task.

## 5. Fallback Strategy

### Main model failure

Failure examples:

* API key missing or invalid.
* Provider timeout.
* Provider returns empty response.
* Provider content filter blocks too many responses.

Fallback:

1. Retry once with the same provider for transient network issues.
2. Switch from direct `deepseek` to OpenRouter DeepSeek route if configured.
3. Switch to `moonshot` or `qwen` depending on task type.
4. If no cloud provider is available, use `ollama` only for low-risk local fallback.
5. Record the fallback in the run log.

### Vision model failure

Fallback:

1. Try another vision-capable route if configured.
2. Ask user to provide source data as text/CSV/PDF instead of screenshot.
3. Mark visual extraction as unavailable rather than hallucinating chart values.

Rule:

* Never infer exact numeric chart values from an image unless OCR/vision output is explicit and confidence is acceptable.

### Long document timeout

Fallback:

1. Split document into chunks.
2. Summarize each chunk with cheaper model.
3. Send condensed notes to long-document model.
4. If still failing, return partial summary with missing sections listed.

### API key missing

Fallback:

1. Skip that provider.
2. Use another configured provider.
3. If no provider is configured, stop before starting the research task.
4. Show a clear setup message pointing to `docs_local/LOCAL_ENV_SETUP.md`.

Rule:

* Missing keys should be `skipped`, not treated as mysterious model failures.

## 6. LLM Health Check Design

Future script idea:

```text
scripts/smoke_test_llm_providers.py
```

Health checks:

| Check | Purpose | Expected result |
| -- | -- | -- |
| API key existence | Confirm required env exists | present / missing / not required |
| Hello test | Minimal text response | short successful answer |
| JSON output test | Validate structured output | parseable JSON object |
| Tool-call test | Confirm agent tool-calling behavior | model can call or simulate required tool schema |
| Vision test | Check chart/image support | only for configured vision-capable models |
| Latency record | Track performance | `latency_ms` per test |

Suggested test prompts:

* Hello: `用一句话回答：Vibe-Trading LLM health check OK。`
* JSON: `只输出 JSON：{"status":"ok","task":"health_check"}`
* Tool call: ask the agent to use a harmless existing read-only capability after a controlled setup.
* Vision: provide a simple static chart image and ask for title/axis/legend extraction.

No health check should print API keys.

## 7. Cost And Quality Logging

Each LLM call should eventually log:

| Field | Meaning |
| -- | -- |
| `provider` | Provider name, such as `deepseek` or `qwen`. |
| `model` | Actual model name. |
| `task_type` | `text_reasoning`, `cheap_summary`, `vision_chart_ocr`, etc. |
| `token_usage` | Provider-reported input/output/total tokens when available. |
| `latency_ms` | End-to-end model call time. |
| `estimated_cost` | Optional estimate based on configured pricing table. |
| `status` | `success`, `failed`, `skipped`, or `fallback_used`. |
| `error_summary` | Redacted short error message. |

Quality notes to record:

* Did the model cite or use data sources?
* Did it follow no-buy/sell-advice boundary?
* Did JSON parse successfully?
* Did it hallucinate unsupported facts?
* Was a fallback used?

## 8. Security Rules

Hard rules:

* Do not commit `agent/.env`.
* Do not print API keys.
* Do not paste keys into chat.
* Do not store real keys in docs.
* Do not default-enable shell tools.
* Keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Keep remote access protected by `API_AUTH_KEY`.
* Do not expose local services to the public internet.

Operational rules:

* Add keys manually to `agent/.env`.
* Restart backend after editing `agent/.env`.
* Use `vibe-trading provider doctor` for redacted diagnostics.
* Treat provider errors as configuration/data problems first, not as reasons to bypass security.

## 9. Recommended Implementation Sequence

1. Configure one main provider only: direct DeepSeek or Qwen/DashScope.
2. Run the minimal research task in `docs_local/MINIMAL_RESEARCH_TASK.md`.
3. Run full US data-source smoke test if needed.
4. Design and implement a small LLM health-check script.
5. Design LLM router data structure.
6. Add router support only after baseline Agent workflow is stable.
7. Plan `a-stock-data` adapter after the original research flow is proven.

## 10. Open Questions

| Question | Owner | Notes |
| -- | -- | -- |
| Should first provider be direct DeepSeek or Qwen/DashScope? | User | Depends on available account/key and cost preference. |
| Which vision route is easiest: Qwen-VL, Kimi Vision, or Gemini? | User/Codex | Needs provider capability verification. |
| Should router be config-only or code-level? | Codex | Decide after minimal research task succeeds. |
| Should cost estimates use manual pricing table? | User/Codex | Provider pricing changes, so keep it auditable and easy to update. |
