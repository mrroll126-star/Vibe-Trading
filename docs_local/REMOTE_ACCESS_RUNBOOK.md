# Remote Access Runbook

Status: prepared on 2026-07-05. Tailscale is not installed on this Mac yet, so the Tailnet dry run has not been executed.

This guide is for starting Vibe-Trading on the home Mac mini and accessing it from another device through Tailscale. It assumes remote access stays inside your private Tailnet and is not exposed to the public internet.

## 1. 本地启动前检查

Run these checks on the Mac mini:

```bash
cd /Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading
git branch --show-current
git status --short
test -f agent/.env && echo "agent/.env exists"
git check-ignore -v agent/.env
tailscale status
tailscale ip -4
```

Confirm:

* You are in the project directory.
* The branch is the expected working branch.
* `agent/.env` exists and is ignored by Git.
* `agent/.env` contains `API_AUTH_KEY`.
* `agent/.env` contains `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Tailscale is installed, logged in, and connected.
* You know the Mac mini Tailscale IP or MagicDNS device name.

Do not continue remote startup if:

* `agent/.env` is missing.
* `API_AUTH_KEY` is missing.
* Shell tools are enabled.
* Tailscale is disconnected.
* You are unsure whether a port is public-facing.

## 2. 在家里 Mac mini 上启动

Preferred after Tailscale is installed:

1. Get the Mac mini Tailscale IP.

```bash
tailscale ip -4
```

2. Set a shell variable for readability.

```bash
TS_IP=<tailscale-ip>
```

3. Start the backend on the Tailscale IP.

```bash
.venv/bin/vibe-trading serve --host "$TS_IP" --port 8899
```

4. In a second terminal, start the frontend on the Tailscale IP.

```bash
cd /Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading/frontend
VITE_API_URL=http://$TS_IP:8899 npm run dev -- --host "$TS_IP" --port 5899
```

If binding directly to the Tailscale IP fails, the fallback is:

```bash
.venv/bin/vibe-trading serve --host 0.0.0.0 --port 8899
```

and:

```bash
cd frontend
VITE_API_URL=http://$TS_IP:8899 npm run dev -- --host 0.0.0.0 --port 5899
```

Use `0.0.0.0` only after confirming `API_AUTH_KEY` exists and shell tools are disabled.

## 3. 在外出设备上访问

From another device logged into the same Tailnet:

```text
http://<tailscale-device-name>:5899
```

or:

```text
http://<tailscale-ip>:5899
```

Backend health URL:

```text
http://<tailscale-device-name>:8899/health
http://<tailscale-ip>:8899/health
```

If MagicDNS is unreliable, use the Tailscale IP first.

## 4. API_AUTH_KEY 怎么用

The key is stored locally in:

```text
agent/.env
```

Look for:

```text
API_AUTH_KEY=...
```

Rules:

* Do not send this key to other people.
* Do not paste the full key into chat.
* Do not commit `agent/.env`.
* If the Web UI asks for an API auth key, copy it from `agent/.env` on your Mac mini and paste it into the UI Settings/auth prompt.
* The frontend stores the key in browser localStorage and sends it as `Authorization: Bearer <key>`.

## 5. 如何停止服务

If the terminal is still open, press `Ctrl+C` in the backend and frontend terminals.

If you need to find the processes:

```bash
lsof -i :8899
lsof -i :5899
```

Then stop a process by PID:

```bash
kill <PID>
```

If a process does not stop:

```bash
kill -9 <PID>
```

Use `kill -9` only as a last resort.

Confirm the ports are closed:

```bash
lsof -i :8899
lsof -i :5899
```

No output means nothing is listening on those ports.

## 6. 常见问题

Page does not open:

* Confirm Tailscale is connected on both devices.
* Try the Tailscale IP instead of MagicDNS.
* Confirm frontend is listening on port `5899`.
* Confirm the Mac is awake and reachable.

API connection failed:

* Confirm backend is listening on port `8899`.
* Open `http://<tailscale-ip>:8899/health`.
* Confirm `VITE_API_URL` points to `http://<tailscale-ip>:8899`.

Authentication failed:

* Confirm `API_AUTH_KEY` is present in `agent/.env`.
* Restart backend after changing `agent/.env`.
* Re-enter the key in the Web UI.
* Do not add extra spaces before or after the key.

CORS error:

* Add the exact frontend origin to `CORS_ORIGINS` in `agent/.env`.
* Example origin: `http://<tailscale-ip>:5899`.
* Do not use `CORS_ORIGINS=*`.
* Restart backend after changing CORS.

Tailscale device offline:

* Open the Tailscale app.
* Confirm the device is logged in.
* Run `tailscale status`.
* Reconnect the device to the same Tailnet.

Port occupied:

```bash
lsof -i :8899
lsof -i :5899
```

Stop the old process or choose a different port.

Shell tools risk:

* Keep `VIBE_TRADING_ENABLE_SHELL_TOOLS=0`.
* Do not enable shell tools for remote access unless you explicitly approve the risk later.

## 7. 安全原则

* Only allow Tailnet access.
* Do not expose the service to the public internet.
* Keep shell tools disabled.
* Do not commit `agent/.env`.
* Do not share `API_AUTH_KEY`.
* Do not paste the key into AI chats.
* Do not store LLM provider keys until you intentionally configure a provider.
* Stop services when you are done using remote access.
