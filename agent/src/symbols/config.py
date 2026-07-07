"""Configuration helpers for symbol normalization."""

from __future__ import annotations

import os


_ENABLED_VALUES = {"1", "true", "yes", "on"}


def is_symbol_normalizer_enabled() -> bool:
    """Return whether tool-entry symbol normalization is enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER", "")
    return value.strip().lower() in _ENABLED_VALUES
