# Test Report

Status: basic local deployment executed on 2026-07-05.

No business code was modified. No real `.env`, token, API key, or OAuth file was created.

## 1. Environment Check

Initial state:

| Check | Result |
| -- | -- |
| Repo path | `/Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading` |
| Branch | `feature/bootstrap-local-setup` |
| Git status before install | `?? docs_local/` |
| System `python3` | Python 3.9.6 |
| System `python` | not found |
| Existing `python3.11` / `python3.12` | not found before install |
| Homebrew | Homebrew 6.0.1 |
| Node.js | v24.16.0 |
| npm | 11.13.0 |
| pnpm | 11.7.0 |
| Docker | not found |

Python 3.11 was installed with Homebrew:

```bash
brew install python@3.11
```

Result:

* Success.
* Python installed as `/opt/homebrew/bin/python3.11`.
* Version: Python 3.11.15.
* System Python was not modified.

## 2. Virtual Environment

Commands:

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/python --version
.venv/bin/pip --version
```

Result:

* Success.
* Virtual environment path: `.venv`.
* Python: 3.11.15.
* pip: 26.1.2.
* `.venv/` is already ignored by `.gitignore`.
* Final `.venv` size: about 955 MB.

## 3. Backend Dependency Install

Commands:

```bash
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e .
```

Result:

* Success.
* Installed editable package `vibe-trading-ai==0.1.10`.
* CLI reports `vibe-trading 0.1.10`.
* No API key was needed for installation.
* No real `.env` was created.

Notes:

* Installation was large but completed with prebuilt macOS arm64 wheels for the main scientific stack.
* No dependency version changes were made.

## 4. Frontend Dependency Install

Lockfile found:

* `frontend/package-lock.json`

Command:

```bash
cd frontend
npm install
```

Result:

* Success.
* Installed 364 packages.
* npm audit found 0 vulnerabilities.
* Warning: `whatwg-encoding@3.1.1` is deprecated.
* Current Node v24.16.0 worked for install.
* Final `frontend/node_modules` size: about 271 MB.

Node note:

* Project Dockerfile uses Node 20.
* If future frontend build/dev errors appear, use Node 20 LTS via nvm.

## 5. Backend Startup

Command:

```bash
.venv/bin/vibe-trading serve --host 127.0.0.1 --port 8899
```

Result:

* Success.
* Backend listened on `127.0.0.1:8899`.
* Server was stopped after validation.
* No shell tools were enabled.
* No remote interface was exposed.

Startup output highlights:

* `Uvicorn running on http://127.0.0.1:8899`
* Warning: no frontend production build found at `frontend/dist`.
* Preflight: LLM provider not configured, so agent research runs cannot function yet.
* Preflight: yfinance failed with curl/OpenSSL TLS error.
* Preflight: OKX reachable, akshare installed, ccxt installed.

Important failure/warning details:

```text
LANGCHAIN_PROVIDER not set in .env (agent cannot function)
yfinance SSLError: curl: (35) TLS connect error ... OPENSSL_internal:invalid library (0)
```

Impact:

* API server can start and health works.
* Full agent research requires LLM provider configuration or Ollama.
* US/HK equity backtest through yfinance may fail until the curl/OpenSSL issue is investigated.

## 6. Frontend Startup

Command:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Result:

* Success.
* Vite started on `http://127.0.0.1:5899/`.
* Web UI HTML was reachable by curl.
* Frontend was stopped after validation.

## 7. Minimal Validation

Commands:

```bash
curl -fsS --max-time 5 http://127.0.0.1:8899/health
curl -fsS --max-time 5 http://127.0.0.1:8899/api
.venv/bin/vibe-trading --help
curl -fsS --max-time 5 http://127.0.0.1:5899/
curl -fsS --max-time 5 http://127.0.0.1:8899/runs
curl -fsS --max-time 5 http://127.0.0.1:5899/sessions
curl -fsS --max-time 5 http://localhost:8899/health
```

Results:

| Check | Result |
| -- | -- |
| Backend `/health` | Success, returned `healthy` |
| Backend `/api` | Success, returned service metadata |
| CLI help | Success |
| Frontend HTML | Success |
| Local protected `/runs` | Success, returned `[]` from loopback dev mode |
| Frontend proxy `/sessions` | Success, returned `[]` |
| `localhost` health | Success |

API auth observation:

* Local loopback access works without `API_AUTH_KEY`.
* Non-local access was not exposed or tested.
* Project code requires `API_AUTH_KEY` for non-local sensitive access.

## 8. Sensitive File Check

Command:

```bash
find . -maxdepth 3 \( -name '.env' -o -name '.env.*' -o -iname '*token*' -o -iname '*oauth*' -o -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' -o -iname '*.duckdb' -o -iname '*.log' \) -not -path './.git/*' -not -path './.venv/*' -not -path './frontend/node_modules/*' -print
```

Result:

* Found only `agent/.env.example` and test files whose names mention token/OAuth.
* No real `.env` was created.
* No token/API key/OAuth/cache/database/log artifact was created in tracked paths.

## 9. Services Stopped

After validation:

* Backend process was stopped with Ctrl+C.
* Frontend process was stopped with Ctrl+C.
* No process was listening on ports 8899 or 5899.

## 10. Failed Or Degraded Items

| Item | Status | Error Summary | Suggested Next Step |
| -- | -- | -- | -- |
| LLM provider | Not configured | `LANGCHAIN_PROVIDER not set` | Choose Ollama, OpenRouter, OpenAI, DeepSeek, or OAuth path; configure only in ignored local env |
| yfinance preflight | Failed | curl/OpenSSL TLS connect error | Investigate `curl_cffi`/cert/OpenSSL issue before relying on yfinance |
| Docker | Not available | `docker: command not found` | Optional: install Docker Desktop later if Docker path is desired |
| Remote access | Not tested | intentionally not exposed | Configure `API_AUTH_KEY` and CORS before Tailscale access |

## 11. Reproduction Commands

Backend:

```bash
source .venv/bin/activate
vibe-trading serve --host 127.0.0.1 --port 8899
```

Frontend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8899 npm run dev -- --host 127.0.0.1 --port 5899
```

Stop:

```bash
Ctrl+C
```
