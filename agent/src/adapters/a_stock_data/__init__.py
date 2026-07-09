"""Helpers for the optional a-stock-data adapter."""

from .financials import (
    fetch_a_stock_financials,
    is_a_stock_financials_fallback_eligible,
    should_try_a_stock_financials_fallback,
)
from .normalizer import normalize_a_stock_financials_result

__all__ = [
    "fetch_a_stock_financials",
    "is_a_stock_financials_fallback_eligible",
    "normalize_a_stock_financials_result",
    "should_try_a_stock_financials_fallback",
]
