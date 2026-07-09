"""Configuration helpers for symbol normalization."""

from __future__ import annotations

import os


_ENABLED_VALUES = {"1", "true", "yes", "on"}
_DISABLED_VALUES = {"0", "false", "no", "off"}


def is_symbol_normalizer_enabled() -> bool:
    """Return whether tool-entry symbol normalization is enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_SYMBOL_NORMALIZER", "")
    return value.strip().lower() in _ENABLED_VALUES


def is_pre_tool_symbol_guard_enabled() -> bool:
    """Return whether pre-tool symbol intent guarding is enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_PRE_TOOL_SYMBOL_GUARD")
    if value is None:
        return True
    return value.strip().lower() not in _DISABLED_VALUES


def is_asset_type_routing_guard_enabled() -> bool:
    """Return whether asset-type-aware tool routing is enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_ASSET_TYPE_ROUTING_GUARD")
    if value is None:
        return True
    return value.strip().lower() not in _DISABLED_VALUES


def is_market_wide_benchmark_policy_enabled() -> bool:
    """Return whether market-wide benchmark policy integration is enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_MARKET_WIDE_BENCHMARK_POLICY", "")
    return value.strip().lower() in _ENABLED_VALUES


def is_a_stock_data_adapter_enabled() -> bool:
    """Return whether optional a-stock-data adapter hooks are enabled."""

    value = os.getenv("VIBE_TRADING_ENABLE_A_STOCK_DATA_ADAPTER", "")
    return value.strip().lower() in _ENABLED_VALUES
