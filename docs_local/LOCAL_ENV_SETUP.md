# Local Environment Setup

Status: placeholder-only guidance. No real `.env`, token, API key, or OAuth file was created.

## 1. Where Config Lives

Use `agent/.env` for this local project. It is project-local and already ignored by Git.

Project behavior found in code and README:

* Web UI Settings writes to `agent/.env`.
* CLI onboarding may create `~/.vibe-trading/.env`.
* Provider loading searches `~/.vibe-trading/.env` -> `agent/.env` -> current directory `.env`.

Do not commit any real env file.

## 2. Supported LLM Providers

Provider metadata comes from `agent/src/providers/llm_providers.json`.

| Provider | Key Env | Base URL Env | Key Required |
| -- | -- | -- | -- |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | Yes |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | Yes |
| OpenAI Codex | none | `OPENAI_CODEX_BASE_URL` | OAuth |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` | Yes |
| Gemini | `GEMINI_API_KEY` | `GEMINI_BASE_URL` | Yes |
| Groq | `GROQ_API_KEY` | `GROQ_BASE_URL` | Yes |
| DashScope / Qwen | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | Yes |
| Zhipu / GLM | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | Yes |
| Moonshot / Kimi | `MOONSHOT_API_KEY` | `MOONSHOT_BASE_URL` | Yes |
| MiniMax | `MINIMAX_API_KEY` | `MINIMAX_BASE_URL` | Yes |
| Xiaomi MIMO | `MIMO_API_KEY` | `MIMO_BASE_URL` | Yes |
| Z.ai | `ZAI_API_KEY` | `ZAI_BASE_URL` | Yes |
| Ollama | none | `OLLAMA_BASE_URL` | No |

## 3. Does It Need A Key To Start?

No. Verified without an LLM key:

* Backend starts.
* Web UI loads.
* `/health` and `/api` work.
* CLI help works.

But real agent research runs require a working LLM provider or local Ollama.

## 4. Placeholder Examples

Ollama:

```bash
LANGCHAIN_PROVIDER=ollama
LANGCHAIN_MODEL_NAME=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434
API_AUTH_KEY=replace_with_strong_random_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

OpenRouter:

```bash
LANGCHAIN_PROVIDER=openrouter
LANGCHAIN_MODEL_NAME=deepseek/deepseek-v4-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=replace_with_your_key
API_AUTH_KEY=replace_with_strong_random_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

OpenAI:

```bash
LANGCHAIN_PROVIDER=openai
LANGCHAIN_MODEL_NAME=gpt-5.5
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace_with_your_key
API_AUTH_KEY=replace_with_strong_random_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

These are examples only. The user should fill real values locally and never commit them.
