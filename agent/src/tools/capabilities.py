"""Shared tool capability gates."""

from __future__ import annotations

import os

SHELL_TOOLS_ENV = "VIBE_TRADING_ENABLE_SHELL_TOOLS"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def env_flag_enabled(name: str) -> bool:
    """Return whether a boolean environment flag is explicitly enabled."""
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def shell_tools_enabled_from_env() -> bool:
    """Return whether shell-capable tools may be registered."""
    return env_flag_enabled(SHELL_TOOLS_ENV)
