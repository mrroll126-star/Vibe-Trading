# Local Environment Setup

Status: LLM provider preparation guidance. `agent/.env` now exists locally and is ignored by Git. It already contains `API_AUTH_KEY` and `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`; do not overwrite those lines. No real LLM provider key has been configured.

## 1. Where Config Lives

Use `agent/.env` for this local project. It is project-local and already ignored by Git.

Project behavior found in code and README:

* Web UI Settings writes to `agent/.env`.
* CLI onboarding may create `~/.vibe-trading/.env`.
* Provider loading searches `~/.vibe-trading/.env` -> `agent/.env` -> current directory `.env`.

Do not commit any real env file.

Current local file:

* Path: `agent/.env`
* Already contains: `API_AUTH_KEY`
* Already contains: `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`
* Does not contain a real LLM provider key yet

When adding an LLM provider, append or edit only the provider-related lines. Do not delete the existing `API_AUTH_KEY` line.

## 2. Supported LLM Providers

Provider metadata comes from `agent/src/providers/llm_providers.json`.

| Provider name | Display name | Key Env | Base URL Env | Default model | Key Required |
| -- | -- | -- | -- | -- | -- |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | `deepseek/deepseek-v4-pro` | Yes |
| `openai` | OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | `gpt-5.5` | Yes |
| `openai-codex` | OpenAI Codex / ChatGPT OAuth | none | `OPENAI_CODEX_BASE_URL` | `openai-codex/gpt-5.3-codex` | OAuth, no API key in `.env` |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` | `deepseek-v4-pro` | Yes |
| `gemini` | Gemini | `GEMINI_API_KEY` | `GEMINI_BASE_URL` | `gemini-3.5-flash` | Yes |
| `groq` | Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` | `meta-llama/llama-4-maverick-17b-128e-instruct` | Yes |
| `dashscope` | DashScope / Qwen | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | `qwen-plus-latest` | Yes |
| `qwen` | Qwen alias | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | `qwen-plus-latest` | Yes |
| `zhipu` | Zhipu | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | `glm-5.1` | Yes |
| `glm` | GLM / Zhipu alias | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | `glm-5.1` | Yes |
| `moonshot` | Moonshot / Kimi | `MOONSHOT_API_KEY` | `MOONSHOT_BASE_URL` | `kimi-k2.6` | Yes |
| `minimax` | MiniMax | `MINIMAX_API_KEY` | `MINIMAX_BASE_URL` | `MiniMax-M3` | Yes |
| `mimo` | Xiaomi MIMO | `MIMO_API_KEY` | `MIMO_BASE_URL` | `MiMo-72B-A27B` | Yes |
| `zai` | Z.ai | `ZAI_API_KEY` | `ZAI_BASE_URL` | `glm-5.1` | Yes |
| `ollama` | Ollama local | none | `OLLAMA_BASE_URL` | `qwen2.5:32b` | No |

Notes:

* Anthropic is not listed as a first-class provider in `agent/src/providers/llm_providers.json`.
* Anthropic models may still be usable through OpenRouter model routing, but the native env pattern in this codebase is OpenRouter: `LANGCHAIN_PROVIDER=openrouter` plus `OPENROUTER_API_KEY`.
* Gemini uses `GEMINI_API_KEY`, not `GOOGLE_API_KEY`, in the current project metadata.

## 3. Recommended First Provider

For a non-programmer setup, the simplest first choices are:

1. OpenRouter, if the user already has an OpenRouter account/key.
2. Ollama, if the user wants local-only testing and already has a strong enough local model installed.
3. OpenAI Codex OAuth, if the user wants to use ChatGPT OAuth and is comfortable running the login command.

Recommended first cloud option: OpenRouter.

Reason:

* One API key can route to several models.
* The project default model is already configured for OpenRouter.
* It is easy to switch models later without changing provider plumbing.

Recommended first local option: Ollama.

Reason:

* No cloud API key.
* Useful for privacy-first testing.
* Requires local model availability and enough machine resources.

## 4. Does It Need A Key To Start?

No. Verified without an LLM key:

* Backend starts.
* Web UI loads.
* `/health` and `/api` work.
* CLI help works.

But real agent research runs require a working LLM provider or local Ollama.

## 5. How To Edit `agent/.env`

Open the file locally:

```bash
open -a TextEdit agent/.env
```

or edit from terminal:

```bash
nano agent/.env
```

Rules:

* Keep the existing `API_AUTH_KEY` line.
* Keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Add only one active LLM provider block at a time.
* Do not paste keys into chat.
* Do not commit `agent/.env`.
* Do not create a root `.env` with secrets.

## 6. Placeholder Examples

Ollama:

```bash
LANGCHAIN_PROVIDER=ollama
LANGCHAIN_MODEL_NAME=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

OpenRouter:

```bash
LANGCHAIN_PROVIDER=openrouter
LANGCHAIN_MODEL_NAME=deepseek/deepseek-v4-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=replace_with_your_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

OpenAI:

```bash
LANGCHAIN_PROVIDER=openai
LANGCHAIN_MODEL_NAME=gpt-5.5
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace_with_your_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

These are examples only. The user should fill real values locally and never commit them.

DeepSeek:

```bash
LANGCHAIN_PROVIDER=deepseek
LANGCHAIN_MODEL_NAME=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=replace_with_your_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

OpenAI Codex OAuth:

```bash
LANGCHAIN_PROVIDER=openai-codex
LANGCHAIN_MODEL_NAME=openai-codex/gpt-5.3-codex
OPENAI_CODEX_BASE_URL=https://chatgpt.com/backend-api/codex/responses
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

Then log in locally:

```bash
.venv/bin/vibe-trading provider login openai-codex
```

## 7. Restart After Editing

After changing `agent/.env`, restart the backend so it reloads the environment.

Backend:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

## 8. Confirm Provider Is Active

CLI diagnostic:

```bash
.venv/bin/vibe-trading provider doctor
```

Expected:

* Provider name is the one you configured.
* Model name is the one you configured.
* API key is shown only as present/redacted.
* No full key is printed.

Web UI:

1. Start backend and frontend.
2. Open `http://127.0.0.1:5899`.
3. Go to Settings.
4. Confirm the provider and model are shown.

Do not run a real research task until the user confirms the provider key has been added locally.

## 9. DeepSeek Verification Result

Date: 2026-07-05.

Configured local values in ignored `agent/.env`:

```bash
LANGCHAIN_PROVIDER=deepseek
LANGCHAIN_MODEL_NAME=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=<stored locally only>
VIBE_TRADING_DEEPSEEK_ADAPTER=auto
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

Security:

* Full key was not printed.
* Full key was not written to docs.
* `agent/.env` remains ignored by Git.
* Shell tools remain disabled.

Provider doctor result:

* Provider: `deepseek`
* Model: `deepseek-v4-pro`
* Base URL: `https://api.deepseek.com`
* API key: set
* `langchain-deepseek`: not installed
* Adapter: OpenAI-compatible fallback, mode `auto`

Minimal direct tests:

| Test | Result |
| -- | -- |
| Hello text | Success: model replied that connection succeeded |
| JSON output | Success: returned JSON-like response |

Current recommendation:

* This DeepSeek setup is good enough for minimal Agent workflow verification.
* Native `langchain-deepseek` is optional later; do not add it until there is a concrete reason.

## 10. Safety Guard Environment Flags

Date: 2026-07-08.

Current defaults:

| Feature | Environment variable | Default | When to change |
| --- | --- | --- | --- |
| Symbol Normalizer | `VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER` | off | Enable only for controlled bare-symbol tests |
| Pre-tool Symbol Intent Guard | `VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD` | on | Disable only for debugging a suspected false positive |
| Asset-type Routing Guard | `VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD` | on | Disable only for debugging a suspected false positive |

Normal local use:

You do not need to add the two safety guard variables to `agent/.env`. They are on by default.

To explicitly disable a safety guard for debugging:

```bash
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=0
VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=0
```

or:

```bash
VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD=false
VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD=false
```

To test Symbol Normalizer:

```bash
VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER=1
```

Security boundary:

Do not commit `agent/.env`. Do not put API keys in documentation or chat. Keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
