# Shell Tool Trace Investigation

## 1. Purpose

This investigation explains why the controlled real Agent run:

```text
run_id: 20260712_204249_68_4f64a5
```

contained trace events for:

```text
bash status=ok
bash status=error
```

even though the run command set:

```text
VIBE_TRADING_ENABLE_SHELL_TOOLS=0
```

This is a read-only investigation. No AgentLoop, shell tool, provider chain,
loader, or Web UI code was changed.

## 2. Finding Summary

Finding:

The `bash` trace events came from the local CLI `vibe-trading run` path, not
from the remote API/session path.

Root cause hypothesis:

```text
vibe-trading run
  -> agent/cli/main.py delegates to cli._legacy.main(...)
  -> cli._legacy.cmd_run(...)
  -> cli._legacy._run_agent(...)
  -> build_registry(..., include_shell_tools=True)
  -> BashTool is registered
  -> AgentLoop executes model-requested bash calls
```

The environment variable `VIBE_TRADING_ENABLE_SHELL_TOOLS` is currently used by
the API/session/swarm request path, but the legacy CLI run path hardcodes
`include_shell_tools=True`.

Therefore, setting `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` on a local
`vibe-trading run` command does not prevent `bash` from being registered.

## 3. Evidence

### Registry policy

`agent/src/tools/__init__.py` defines shell-capable tools:

```text
_SHELL_TOOL_NAMES = {"bash", "background_run"}
```

The registry excludes them only when:

```text
include_shell_tools=False
```

### Bash tool implementation

`agent/src/tools/bash_tool.py` defines:

```text
class BashTool(BaseTool):
    name = "bash"
    is_readonly = False
```

It executes shell commands through `subprocess.run(..., shell=True, ...)`.

### API/session gate

`agent/api_server.py` uses:

```text
_shell_tools_enabled_for_request(request)
```

which returns:

```text
_env_shell_tools_enabled()
```

The env flag is:

```text
VIBE_TRADING_ENABLE_SHELL_TOOLS
```

API session messages and API swarm runs pass this value into
`include_shell_tools`.

### CLI run path

`agent/cli/main.py` delegates non-interactive commands such as
`vibe-trading run -p ...` to `cli._legacy.main(...)`.

`agent/cli/_legacy.py` constructs the AgentLoop registry with:

```text
build_registry(..., include_shell_tools=True, ...)
```

This is independent of `VIBE_TRADING_ENABLE_SHELL_TOOLS`.

## 4. Trace Source Analysis

Trace:

```text
agent/runs/20260712_204249_68_4f64a5/trace.jsonl
```

Observed `bash` events:

| Event | Tool | Status | Command preview | Interpretation |
| --- | --- | --- | --- | --- |
| tool_call + tool_result | bash | ok | `ls -la .../agent/runs/20260712_204249_68_4f64a5/` | real shell command executed successfully |
| tool_call + tool_result | bash | error | `python3 /tmp/fetch_catl.py 2>&1` | real shell command attempted and failed |

The trace events are real `tool_call` / `tool_result` entries. They are not
just log labels.

## 5. Shell Permission Analysis

Confirmed:

* `bash` is a shell-capable tool.
* `bash` is supposed to be excluded when `include_shell_tools=False`.
* API/session paths respect `VIBE_TRADING_ENABLE_SHELL_TOOLS`.
* The local legacy CLI run path hardcodes `include_shell_tools=True`.
* AgentLoop does not apply a second shell permission gate at execution time; it
  executes whatever is registered in the registry.

Not confirmed in this read-only investigation:

* Whether all local interactive CLI paths intentionally allow shell tools.
* Whether this behavior is documented as intended for trusted local CLI only.
* Whether a previous upstream design expects local CLI to always include shell
  tools regardless of env var.

## 6. Risk Assessment

Risk level:

```text
High for unattended local Agent runs.
Medium for trusted manual local CLI use.
Critical if this behavior were reachable from remote/API sessions.
```

Why:

* `bash` can execute host commands as the current user.
* A research prompt can lead the model to inspect files or run scripts.
* This violates this local project's safety expectation that
  `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` disables shell-capable tools.

Mitigating facts:

* The remote API/session path appears to use the env gate correctly.
* This observed run used the local CLI `vibe-trading run` path.
* Sensitive/runtime files were not committed.

## 7. Recommended Fix Plan

Recommended priority:

```text
P0 before remote/unattended use
P1 before Research Workspace productionization
```

Recommended fix direction:

1. Add one shared helper for shell-tool opt-in, for example:

```text
shell_tools_enabled_from_env()
```

2. Use that helper in:

```text
agent/api_server.py
agent/cli/_legacy.py
agent/cli/main.py interactive path if applicable
swarm CLI entrypoints if applicable
```

3. Change `vibe-trading run` so `include_shell_tools` is false unless the
operator explicitly opts in.

4. Add tests:

* `vibe-trading run` default does not register `bash`.
* `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` does not register `bash`.
* `VIBE_TRADING_ENABLE_SHELL_TOOLS=1` registers `bash` for local CLI if that
  behavior is intentionally allowed.
* API/session existing shell-tool tests continue to pass.

5. Consider adding a trace-level audit warning if a shell tool is registered or
executed.

## 8. Recommended Operational Policy

Until fixed:

* Do not use `vibe-trading run` for unattended research tasks where shell tools
  must be disabled.
* Prefer direct tool-level observation scripts or API/session paths that are
  already gated by `VIBE_TRADING_ENABLE_SHELL_TOOLS`.
* Do not expose the local CLI run path through remote automation.
* Treat any trace containing `bash` as requiring safety review before it is used
  as a production artifact proof.

## 9. Conclusion

The likely root cause is confirmed at the code-path level:

```text
legacy CLI run hardcodes include_shell_tools=True
```

The `VIBE_TRADING_ENABLE_SHELL_TOOLS=0` flag did not protect this local CLI run.

This should be fixed before using real Agent runs as the default Research
Workspace production path.
