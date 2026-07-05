# Current Architecture

Status: read-only discovery updated on 2026-07-05. No business code was changed.

## 1. Runtime

* Backend: Python FastAPI application in `agent/api_server.py`, served by uvicorn.
* Frontend: React 19 + TypeScript + Vite application in `frontend/`.
* CLI: yes. Console command is `vibe-trading`, configured in `pyproject.toml`.
* MCP: yes. Console command is `vibe-trading-mcp`, implemented by `agent/mcp_server.py`.
* Docker: yes. Multi-stage Dockerfile builds frontend first, then runs Python 3.11 runtime.
* Local venv: supported and verified. `pyproject.toml` requires Python `>=3.11`; local `.venv` now uses Python 3.11.15 and `pip install -e .` succeeded.
* Node.js: required for frontend development and frontend build. Docker uses `node:20-slim`; README says Node is needed for Web UI dev.
* Current machine note: system Python is 3.9.6, which is below the project requirement. Homebrew Python 3.11.15 is installed and used only for this project's `.venv`.

## 2. Important Entry Points

* Backend entry: `agent/api_server.py`, especially `serve_main()`.
* CLI entry: `agent/cli/main.py`, with legacy command handling in `agent/cli/_legacy.py`.
* MCP entry: `agent/mcp_server.py`.
* Frontend entry: `frontend/src/main.tsx`, configured by `frontend/vite.config.ts`.
* Config files:
  * Python package: `pyproject.toml`
  * Python dependency snapshot: `agent/requirements.txt`
  * Frontend package: `frontend/package.json`
  * Frontend lockfile: `frontend/package-lock.json`
  * Environment template: `agent/.env.example`
  * Docker: `Dockerfile`, `docker-compose.yml`
  * Git ignore rules: `.gitignore`, `frontend/.gitignore`, `agent/.gitignore`
* Docker startup entry:
  * Dockerfile command: `vibe-trading serve --host 0.0.0.0 --port 8899`
  * Compose publishes backend as `127.0.0.1:8899:8899`.

## 3. Data Source Layer

Data sources are organized as loaders under `agent/backtest/loaders/`. The central registry is `agent/backtest/loaders/registry.py`.

### A-share

* Existing providers: `tencent`, `mootdx`, `eastmoney`, `baostock`, `akshare`, `tushare`, `futu`, `local`.
* Provider files:
  * `agent/backtest/loaders/tencent_loader.py`
  * `agent/backtest/loaders/mootdx_loader.py`
  * `agent/backtest/loaders/eastmoney_loader.py`
  * `agent/backtest/loaders/baostock_loader.py`
  * `agent/backtest/loaders/akshare_loader.py`
  * `agent/backtest/loaders/tushare.py`
  * `agent/backtest/loaders/futu.py`
  * `agent/backtest/loaders/local_loader.py`
* Fallback order, by code: `tencent`, `mootdx`, `eastmoney`, `baostock`, `akshare`, `tushare`, `local`.
* API key or local service:
  * No key: `tencent`, `mootdx`, `eastmoney`, `baostock`, `akshare`, `local` if configured.
  * Requires token or local service: `tushare` requires `TUSHARE_TOKEN`; `futu` requires local FutuOpenD and is not in the A-share fallback chain.
* Symbol format:
  * Common project format: `600519.SH`, `000001.SZ`, `430139.BJ`.
  * BaoStock also accepts native `sh.601398` / `sz.000001`.
  * Mootdx accepts `.SH/.SZ/.BJ` suffix or bare 6-digit tickers.
* Known limitations: public sources can be rate-limited or blocked; Tushare is richer but token-gated; Futu needs a local gateway.

### US stocks

* Existing providers: `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, `tiingo`, `fmp`, `finnhub`, `alphavantage`, `akshare`, `local`.
* Provider files:
  * `agent/backtest/loaders/yahoo_loader.py`
  * `agent/backtest/loaders/stooq_loader.py`
  * `agent/backtest/loaders/sina_loader.py`
  * `agent/backtest/loaders/eastmoney_loader.py`
  * `agent/backtest/loaders/yfinance_loader.py`
  * `agent/backtest/loaders/tiingo_loader.py`
  * `agent/backtest/loaders/fmp_loader.py`
  * `agent/backtest/loaders/finnhub_loader.py`
  * `agent/backtest/loaders/alphavantage_loader.py`
  * `agent/backtest/loaders/akshare_loader.py`
  * `agent/backtest/loaders/local_loader.py`
* Fallback order, by code: `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, `tiingo`, `fmp`, `finnhub`, `alphavantage`, `akshare`, `local`.
* Providers requiring API key: `tiingo` (`TIINGO_API_KEY`), `fmp` (`FMP_API_KEY`), `finnhub` (`FINNHUB_API_KEY`), `alphavantage` (`ALPHAVANTAGE_API_KEY`).
* Providers working without API key: `yahoo`, `stooq`, `sina`, `eastmoney`, `yfinance`, `akshare`, `local` if configured.
* Symbol format:
  * Registry auto-detection expects normalized US symbols like `AAPL.US`.
  * Some loader internals strip `.US` and call vendor APIs with `AAPL`.
  * README notes swarm grounding may promote bare US tickers like `NVDA` to `NVDA.US`.
* Known limitations: current loader layer is historical OHLCV focused. Quote/latest price, fundamentals, earnings, options, and SEC data are separate tools, not necessarily the same loader interface.

### HK stocks

* Existing providers: `eastmoney`, `yahoo`, `futu`, `yfinance`, `akshare`, `local`.
* Provider files:
  * `agent/backtest/loaders/eastmoney_loader.py`
  * `agent/backtest/loaders/yahoo_loader.py`
  * `agent/backtest/loaders/futu.py`
  * `agent/backtest/loaders/yfinance_loader.py`
  * `agent/backtest/loaders/akshare_loader.py`
  * `agent/backtest/loaders/local_loader.py`
* Fallback order, by code: `eastmoney`, `yahoo`, `futu`, `yfinance`, `akshare`, `local`.
* API key or local service:
  * No key: `eastmoney`, `yahoo`, `yfinance`, `akshare`, `local` if configured.
  * Requires local service: `futu` requires local FutuOpenD.
* Symbol format:
  * Common project format: `00700.HK`, `700.HK`.
  * Futu maps to forms like `HK.00700`.
* Known limitations: Futu availability depends on local OpenD; public sources may be rate-limited.

### Local data

* Existing local provider: `agent/backtest/loaders/local_loader.py`.
* File formats supported: CSV, Parquet, DuckDB.
* Config path: `~/.vibe-trading/data-bridge/config.yaml`.
* Symbol usage: can use `local:` prefix, for example `local:AAPL.US`.
* Cache/storage location:
  * Optional loader cache is controlled by `VIBE_TRADING_DATA_CACHE=1`.
  * Cache files live under `~/.vibe-trading/cache/loaders/`.
  * Cache is off by default.
* Important behavior: explicit `local` does not silently fall back to network sources.

## 4. Agent / Tool Layer

* Skills:
  * Bundled skills live in `agent/src/skills/*/SKILL.md`.
  * One older/local-style skill folder exists at `agent/skills/ashare-mootdx/`.
  * User-created skills are referenced in code as `~/.vibe-trading/skills/user/`.
* Tools:
  * Tool registry is `agent/src/tools/__init__.py`.
  * Individual tools live in `agent/src/tools/`.
  * Tool classes are auto-discovered from files in that folder.
* MCP tools:
  * MCP server is `agent/mcp_server.py`.
  * MCP exposes skills, research goals, market data, backtest/factor/options/pattern tools, financial data tools, read-only connector reads, swarm orchestration, and trade journal/shadow-account analysis.
* Swarm workflows:
  * Presets live in `agent/src/swarm/presets/*.yaml`.
  * Runtime code lives in `agent/src/swarm/`.
* Dangerous tools:
  * `bash` and `background_run` are shell-capable tools.
  * File write/code generation tools include `write_file`, `edit_file`, backtest/shadow code generation surfaces, and upload/document readers with path controls.
* Disabled by default:
  * Shell tools are disabled unless `VIBE_TRADING_ENABLE_SHELL_TOOLS` is explicitly enabled.
  * API code calls `build_registry(... include_shell_tools=False)` unless the explicit flag is active.

## 5. Backtest / Strategy Layer

* Backtest files: `agent/backtest/`.
* Main runner: `agent/backtest/runner.py`.
* Engines:
  * `agent/backtest/engines/china_a.py`
  * `agent/backtest/engines/global_equity.py`
  * `agent/backtest/engines/crypto.py`
  * `agent/backtest/engines/futures_base.py`
  * `agent/backtest/engines/options_portfolio.py`
  * plus composite and market-specific engines.
* Data loaders: `agent/backtest/loaders/`.
* Alpha zoo files: `agent/src/factors/zoo/`.
* Factor registry and analysis: `agent/src/factors/`.

## 6. Web / API

* Backend port:
  * Verified local command: `vibe-trading serve --host 127.0.0.1 --port 8899`.
  * CLI default varies by entry path: `serve_main()` default is 8000; README and dev scripts commonly use 8899.
  * `scripts/dev` default backend port is 8899.
  * Docker exposes 8899.
* Frontend port:
  * Verified local command: `VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899`.
  * Vite config and `scripts/dev` default to 5899.
  * Some older README/CORS defaults still include 5173 as a common Vite port.
* API server file: `agent/api_server.py`.
* Auth:
  * `API_AUTH_KEY` is read by `agent/api_server.py`.
  * Local loopback clients are allowed in dev mode.
  * Non-local clients require `API_AUTH_KEY`; otherwise sensitive endpoints return 403.
  * Most run/session/swarm/live/settings/upload routes are protected by `require_auth`, `require_event_stream_auth`, or local-or-auth checks.
* CORS:
  * Configured by `CORS_ORIGINS`.
  * Defaults include localhost and 127.0.0.1 on ports 3000, 5173, and 8000.
  * Wildcard `*` is rejected when credentials are enabled.
* Serve command:
  * Local API only: `vibe-trading serve --host 127.0.0.1 --port 8899`.
  * Dev helper: `scripts/dev up`.
  * Docker: `docker compose up --build`.
* Localhost vs 0.0.0.0:
  * `127.0.0.1` is local-only.
  * `0.0.0.0` binds all interfaces. The API still rejects non-local sensitive requests without `API_AUTH_KEY`, but this should not be used for remote access until authentication and CORS are configured.
* Tailscale considerations:
  * For Tailnet access, bind intentionally and set `API_AUTH_KEY`.
  * Add explicit CORS origins for the Tailscale URL if using a separate frontend origin.
  * Do not expose the same port to the public internet.

## 7. Storage / Cache

* Project-local runtime directories:
  * `agent/runs/`
  * `agent/sessions/`
  * `agent/uploads/`
  * `agent/.swarm/runs/`
  * `agent/.ui_runtime/`
  * `agent/.tasks/`
* User-home state:
  * `~/.vibe-trading/.env`
  * `~/.vibe-trading/sessions.db`
  * `~/.vibe-trading/cache/loaders/`
  * `~/.vibe-trading/data-bridge/config.yaml`
  * `~/.vibe-trading/uploads/`
  * `~/.vibe-trading/imports/`
  * `~/.vibe-trading/shadow_runs/`
* Docker volumes:
  * `vibe-runs`
  * `vibe-sessions`
  * `vibe-home`
  * `vibe-swarm-runs`
  * `vibe-uploads`
* Files ignored by git:
  * `.env`, `agent/.env`, `.venv/`, `agent/.venv/`, `node_modules/`
  * `local_reports/`
  * `agent/sessions/`, `agent/runs/`, `agent/uploads/`, `agent/.swarm/runs/`
  * `.cache/`, `.vibe-dev/`, `data/*.duckdb`, `data/parquet/`, logs under `data/`
  * `frontend/dist/`, build artifacts, test result JSON.
* Gap noted: `.env.*`, generic `*.sqlite`, and generic `*.duckdb` are not broadly covered yet. Add ignore rules before generating local databases.

## 8. Modified Files

* Files intentionally modified from upstream: none in business code.
* Files added locally: `docs_local/*`, `scripts/smoke_test_us_data_sources.py`.
* Local ignore addition: `.gitignore` now ignores `local_reports/`.
* Files that should avoid modification without approval:
  * `agent/backtest/loaders/registry.py`
  * existing provider files under `agent/backtest/loaders/`
  * auth logic in `agent/api_server.py`
  * tool safety/path logic under `agent/src/tools/`
  * trading connector execution logic under `agent/src/trading/` and `agent/src/live/`

## 9. Known Risks

* Risk: System Python is 3.9.6, but project requires Python 3.11+.
  * Mitigation: Homebrew Python 3.11.15 is installed and `.venv` uses it.
* Risk: Current Node is v24.16.0, while Docker uses Node 20 and frontend tooling may be better tested on Node 20/22.
  * Mitigation: use Node 20 LTS if frontend install/build fails.
* Risk: Docker is not installed on this machine.
  * Mitigation: prefer local Python/Node path first, or install Docker Desktop later.
* Risk: LLM features need an LLM provider API key or local Ollama.
  * Mitigation: start with health/API/static UI checks; configure LLM only when needed.
* Risk: yfinance preflight failed with a curl/OpenSSL TLS error.
  * Mitigation: investigate `curl_cffi`, certificate, and OpenSSL linkage before relying on yfinance for US/HK research.
* Risk: some data sources require API keys or local services.
  * Mitigation: smoke test should record skipped providers instead of failing.
* Risk: remote access without `API_AUTH_KEY` is blocked and unsafe to expose.
  * Mitigation: set a strong `API_AUTH_KEY` before Tailscale/LAN access.
* Risk: shell tools can execute commands on the host.
  * Mitigation: keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Risk: macOS arm64 native dependencies such as WeasyPrint/Pango may need system libraries.
  * Mitigation: record install failures exactly during the next dependency step.

## 10. Open Questions

* Question: Which local Python 3.11+ tool should be used, pyenv or uv?
  * Owner: user/Codex next deployment step.
* Question: Should we create a local `.env.example.local` with placeholders?
  * Owner: user approval.
* Question: Which LLM path should be used for first run: Ollama, OpenRouter, OpenAI, DeepSeek, or ChatGPT OAuth?
  * Owner: user.
