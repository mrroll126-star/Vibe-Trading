"""Shared symbol normalization helpers.

This package is intentionally not wired into tools or loaders yet.  It provides
pure, rule-based helpers that future tool-layer integration can reuse.
"""

from src.symbols.normalizer import NormalizedSymbol, normalize_many, normalize_symbol
from src.symbols.intent_guard import evaluate_symbol_intent_guard

__all__ = [
    "NormalizedSymbol",
    "evaluate_symbol_intent_guard",
    "normalize_many",
    "normalize_symbol",
]
