"""Shell tool capability gate tests."""

from __future__ import annotations

import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.tools import build_registry
from src.tools.capabilities import (
    SHELL_TOOLS_ENV,
    shell_tools_enabled_from_env,
)


class ShellToolCapabilityTests(unittest.TestCase):
    def test_default_env_disables_shell_tools(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(SHELL_TOOLS_ENV, None)
            self.assertFalse(shell_tools_enabled_from_env())
            registry = build_registry(include_shell_tools=shell_tools_enabled_from_env())
        self.assertNotIn("bash", registry.tool_names)
        self.assertNotIn("background_run", registry.tool_names)

    def test_explicit_zero_disables_shell_tools(self) -> None:
        with patch.dict(os.environ, {SHELL_TOOLS_ENV: "0"}, clear=False):
            self.assertFalse(shell_tools_enabled_from_env())
            registry = build_registry(include_shell_tools=shell_tools_enabled_from_env())
        self.assertNotIn("bash", registry.tool_names)
        self.assertNotIn("background_run", registry.tool_names)

    def test_explicit_one_enables_shell_tools(self) -> None:
        with patch.dict(os.environ, {SHELL_TOOLS_ENV: "1"}, clear=False):
            self.assertTrue(shell_tools_enabled_from_env())
            registry = build_registry(include_shell_tools=shell_tools_enabled_from_env())
        self.assertIn("bash", registry.tool_names)
        self.assertIn("background_run", registry.tool_names)

    def test_cli_run_registry_path_defaults_to_no_shell_tools(self) -> None:
        captured: dict[str, object] = {}
        legacy = importlib.import_module("cli._legacy")

        def fake_build_registry(**kwargs: object) -> object:
            captured.update(kwargs)
            return object()

        class FakeAgentLoop:
            def __init__(self, **kwargs: object) -> None:
                self.memory = SimpleNamespace(run_dir=None)

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(SHELL_TOOLS_ENV, None)
            with patch("src.tools.build_registry", side_effect=fake_build_registry), \
                patch("src.providers.chat.ChatLLM", return_value=object()), \
                patch("src.agent.loop.AgentLoop", FakeAgentLoop), \
                patch("src.memory.persistent.PersistentMemory", return_value=object()), \
                patch("src.config.loader.load_agent_config", return_value=None), \
                patch.object(legacy, "_run_with_graceful_cancel", return_value={"status": "success"}):
                legacy._run_agent("test prompt", stream_output=False)

        self.assertIs(captured.get("include_shell_tools"), False)

    def test_cli_run_registry_path_allows_explicit_shell_opt_in(self) -> None:
        captured: dict[str, object] = {}
        legacy = importlib.import_module("cli._legacy")

        def fake_build_registry(**kwargs: object) -> object:
            captured.update(kwargs)
            return object()

        class FakeAgentLoop:
            def __init__(self, **kwargs: object) -> None:
                self.memory = SimpleNamespace(run_dir=None)

        with patch.dict(os.environ, {SHELL_TOOLS_ENV: "1"}, clear=False):
            with patch("src.tools.build_registry", side_effect=fake_build_registry), \
                patch("src.providers.chat.ChatLLM", return_value=object()), \
                patch("src.agent.loop.AgentLoop", FakeAgentLoop), \
                patch("src.memory.persistent.PersistentMemory", return_value=object()), \
                patch("src.config.loader.load_agent_config", return_value=None), \
                patch.object(legacy, "_run_with_graceful_cancel", return_value={"status": "success"}):
                legacy._run_agent("test prompt", stream_output=False)

        self.assertIs(captured.get("include_shell_tools"), True)

    def test_api_session_shell_gate_keeps_env_behavior(self) -> None:
        api_server = importlib.import_module("api_server")
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(SHELL_TOOLS_ENV, None)
            self.assertFalse(api_server._shell_tools_enabled_for_request(request))

        with patch.dict(os.environ, {SHELL_TOOLS_ENV: "0"}, clear=False):
            self.assertFalse(api_server._shell_tools_enabled_for_request(request))

        with patch.dict(os.environ, {SHELL_TOOLS_ENV: "1"}, clear=False):
            self.assertTrue(api_server._shell_tools_enabled_for_request(request))


if __name__ == "__main__":
    unittest.main()
