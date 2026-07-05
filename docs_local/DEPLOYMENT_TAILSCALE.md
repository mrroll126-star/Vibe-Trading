# Tailscale Deployment Plan

Status: plan plus local-port verification. No service has been exposed remotely, no `.env` was created, and no remote access was enabled.

## 1. Recommended Local Run Mode

For the next deployment step, prefer local Python/Node first because Docker is not installed on this machine.

Verified development ports:

* Backend: `8899`, verified on `127.0.0.1:8899`
* Frontend: `5899`, verified on `127.0.0.1:5899`

Repository helper:

```bash
scripts/dev up
```

What it does:

* Starts backend on `127.0.0.1:8899` by default.
* Starts frontend on `127.0.0.1:5899` by default.
* Uses `VITE_API_URL=http://127.0.0.1:8899` for frontend-to-backend proxying.
* Writes local dev logs and pid files under `.vibe-dev/`, which is already ignored by Git.

Manual equivalent, verified:

```bash
vibe-trading serve --host 127.0.0.1 --port 8899
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5899
```

Production-style single-server option after frontend build:

```bash
cd frontend
npm run build
cd ..
vibe-trading serve --host 127.0.0.1 --port 8899
```

## 2. Tailscale Access URL Shape

After the user explicitly approves remote access and configures authentication, remote devices in the same Tailnet could use:

```text
http://<tailscale-device-name>:8899
http://<tailscale-ip>:8899
http://<tailscale-device-name>:5899
http://<tailscale-ip>:5899
```

Recommended long-term shape:

* Use MagicDNS device name where possible.
* Keep access inside Tailnet only.
* Do not expose the service to the public internet.
* Prefer serving the built frontend from backend port `8899` for simpler CORS and auth.

## 3. Authentication

Remote access must use `API_AUTH_KEY`.

The backend reads:

```text
API_AUTH_KEY
```

Expected request behavior:

* Local loopback clients can work in development mode.
* Non-local clients need `Authorization: Bearer <API_AUTH_KEY>` for sensitive API calls.
* Browser EventSource streams may use query-string key handling through project code, normally managed by Web UI Settings after the user enters the key.

Recommended placeholder-only sample for a future `.env.example.local`:

```bash
API_AUTH_KEY=replace_with_strong_random_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
CORS_ORIGINS=http://localhost:5899,http://127.0.0.1:5899,http://<tailscale-device-name>:5899
```

Do not create or commit a real `agent/.env`.

## 4. Frontend API URL

Frontend dev server uses `frontend/vite.config.ts`.

Default:

```text
VITE_API_URL=http://127.0.0.1:8899
```

For remote frontend development, the frontend must proxy to a backend URL reachable from the device/browser. Examples:

```bash
VITE_API_URL=http://<tailscale-device-name>:8899 npm run dev -- --host 0.0.0.0 --port 5899
```

Simpler option:

* Build the frontend.
* Let FastAPI serve `frontend/dist` from the backend.
* Access only backend port `8899` over Tailscale.

## 5. Bind Address Choices

| Bind address | Meaning | Risk | Recommendation |
| -- | -- | -- | -- |
| `127.0.0.1` | Only same machine can connect | Lowest | Best for local testing |
| `localhost` | Same practical meaning for browser use | Low | Fine for local testing |
| Tailscale IP | Only that interface listens | Medium | Good future option if supported by command |
| `0.0.0.0` | All network interfaces listen | Higher | Use only after `API_AUTH_KEY` and CORS are set |

Code note:

* API code warns when binding non-loopback without `API_AUTH_KEY`.
* Sensitive non-local requests are rejected without `API_AUTH_KEY`.
* A bound port is still visible on the network, so authentication is required before remote access.

## 6. CORS

Backend uses `CORS_ORIGINS`.

Defaults include:

* `http://localhost:3000`
* `http://localhost:5173`
* `http://localhost:8000`
* `http://127.0.0.1:3000`
* `http://127.0.0.1:5173`
* `http://127.0.0.1:8000`

For this repo's current dev helper, add:

```text
http://localhost:5899
http://127.0.0.1:5899
http://<tailscale-device-name>:5899
http://<tailscale-ip>:5899
```

Important:

* Do not use `CORS_ORIGINS=*`.
* Code rejects wildcard CORS while credentials are enabled.
* If frontend is served by backend from the same origin, CORS is simpler.

## 7. Shell Tools

Keep shell tools disabled:

```text
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

Reason:

* Shell tools can execute commands on the local machine as the API process user.
* Remote browser/API access plus shell tools is a much higher-risk combination.

If future work truly needs shell tools:

1. Explain the exact use case.
2. Explain the risk.
3. Set narrow allowed roots.
4. Require explicit user confirmation before enabling.

## 8. Why Not Public Internet

Do not expose this service directly to the public internet because it may handle:

* LLM API credentials.
* Local files and uploaded documents.
* Research reports and trading journals.
* Broker connector configuration.
* Future trading-related connectors.

Tailscale gives a private Tailnet path without opening a public port.

## 9. Troubleshooting Plan

Local browser cannot open:

1. Check backend health: `curl http://127.0.0.1:8899/health`.
2. Check frontend: `http://127.0.0.1:5899`.
3. Check `.vibe-dev/logs/` if using `scripts/dev`.
4. Check whether ports 8899 or 5899 are occupied.

Tailscale device cannot open:

1. Confirm service is bound to a non-loopback interface only after approval.
2. Confirm Tailnet connectivity between devices.
3. Use Tailscale IP first, then MagicDNS.
4. Confirm local firewall is not blocking.

Auth failure:

1. Confirm `API_AUTH_KEY` is set on backend.
2. Restart backend after changing env.
3. Confirm frontend has stored/sends the same key.
4. Test API with `Authorization: Bearer <key>`.

CORS failure:

1. Identify browser origin from devtools.
2. Add exact origin to `CORS_ORIGINS`.
3. Do not use wildcard.
4. Restart backend.

Port occupied:

1. Change `VIBE_BACKEND_PORT` or `VIBE_FRONTEND_PORT` for `scripts/dev`.
2. Or pass `--port` manually to backend/frontend commands.

## 10. Dry Run Preparation

Verified local ports:

* Backend: `127.0.0.1:8899`
* Frontend: `127.0.0.1:5899`
* Local UI: `http://127.0.0.1:5899`
* Local health: `http://127.0.0.1:8899/health`
* Local API info: `http://127.0.0.1:8899/api`

Authentication behavior from code:

* Loopback clients are trusted for local development.
* Non-local sensitive API requests require `API_AUTH_KEY`.
* If no key is set and the client is non-local, sensitive routes return 403.
* If a key is set and the token is missing or wrong, protected requests return 401.

Tailscale bind options:

* Safer targeted option: bind backend/frontend to the Mac's Tailscale IP if the startup command accepts it.
* Simpler option: bind to `0.0.0.0` only after setting `API_AUTH_KEY`, explicit CORS origins, and keeping shell tools off.
* Do not bind non-local interfaces before authentication is configured.

Next dry run plan, not yet executed:

1. Create a local ignored `agent/.env` manually.
2. Set a strong `API_AUTH_KEY`.
3. Keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
4. Add explicit `CORS_ORIGINS` for local and Tailscale frontend origins.
5. Start backend on a Tailscale-reachable bind address.
6. Start frontend on a Tailscale-reachable bind address, with `VITE_API_URL` pointing to the backend Tailscale URL.
7. From another Tailscale device, open the frontend URL.
8. Verify unauthenticated sensitive requests fail.
9. Enter/use the API key and verify authenticated requests succeed.
10. Stop both services after the test.

Example placeholder-only env values:

```bash
API_AUTH_KEY=replace_with_strong_random_key
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
CORS_ORIGINS=http://127.0.0.1:5899,http://localhost:5899,http://replace-device-name:5899,http://replace-tailscale-ip:5899
```
