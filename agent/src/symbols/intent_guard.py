"""Pure pre-tool symbol intent guard.

This module does not execute tools, call providers, perform network requests,
or read/write files.  It only compares a user's original prompt with a proposed
tool call to decide whether the symbol intent is auditable enough to proceed.
"""

from __future__ import annotations

import re
from typing import Any

from src.symbols.normalizer import normalize_symbol


_SUPPORTED_TOOL = "get_market_data"
_DECISION_RANK = {"allow": 0, "block": 1, "clarify": 2}
_SYMBOL_KEYS = ("codes", "symbols", "symbol", "ticker", "code")
_CHINESE_NAME_KEYWORDS = {
    "贵州茅台": "600519.SH",
    "平安银行": "000001.SZ",
    "苹果公司": "AAPL.US",
}
_AMBIGUOUS_000001_HINTS = {
    "000001.SZ",
    "000001.SH",
    "平安银行",
    "上证指数",
    "上证综指",
    "SSE COMPOSITE",
}


def evaluate_symbol_intent_guard(
    original_prompt: str,
    tool_name: str,
    tool_args: dict,
    recent_symbol_search_results: list | None = None,
) -> dict:
    """Evaluate whether a tool symbol is traceable to the original prompt.

    Args:
        original_prompt: The user's original message before LLM tool planning.
        tool_name: Name of the tool the LLM wants to call.
        tool_args: Proposed tool-call arguments.
        recent_symbol_search_results: Reserved for a future audited search policy.

    Returns:
        A JSON-serializable decision dictionary.
    """
    del recent_symbol_search_results  # Not used by the MVP policy.

    if tool_name != _SUPPORTED_TOOL:
        return _decision(
            "allow",
            "unsupported_tool_for_mvp",
            "unsupported_tool_for_mvp",
            tool_name=tool_name,
            tool_symbol=None,
            raw_symbol_candidates=[],
            warnings=[],
            metadata={"source": "unsupported_tool"},
            details=[],
        )

    prompt = "" if original_prompt is None else str(original_prompt)
    symbols = _extract_tool_symbols(tool_args)
    if not symbols:
        return _decision(
            "block",
            "missing_tool_symbol",
            "missing_tool_symbol",
            tool_name=tool_name,
            tool_symbol=None,
            raw_symbol_candidates=[],
            warnings=["get_market_data requires at least one auditable symbol."],
            metadata={"source": "untraceable"},
            details=[],
        )

    prompt_facts = _extract_prompt_facts(prompt)
    details = [_evaluate_one_symbol(prompt, prompt_facts, symbol) for symbol in symbols]
    overall = max(details, key=lambda item: _DECISION_RANK[item["decision"]])
    warnings: list[str] = []
    raw_candidates: list[str] = []
    for item in details:
        warnings.extend(item.get("warnings") or [])
        raw_candidates.extend(item.get("raw_symbol_candidates") or [])

    return _decision(
        overall["decision"],
        overall["reason"],
        overall["matched_rule"],
        tool_name=tool_name,
        tool_symbol=symbols[0] if len(symbols) == 1 else ",".join(symbols),
        raw_symbol_candidates=_unique(raw_candidates),
        warnings=_unique(warnings),
        metadata=overall.get("metadata") or {},
        details=details,
    )


def _evaluate_one_symbol(prompt: str, facts: dict[str, Any], tool_symbol: str) -> dict:
    upper_symbol = tool_symbol.upper()

    if upper_symbol in facts["explicit_symbols"]:
        return _symbol_decision(
            "allow",
            "explicit_symbol_match",
            "rule_a_explicit_symbol",
            tool_symbol,
            raw=[upper_symbol],
            source="explicit",
            normalized_symbol=upper_symbol,
        )

    if facts["explicit_symbols"]:
        return _symbol_decision(
            "block",
            "tool_symbol_mismatch",
            "rule_e_tool_symbol_mismatch",
            tool_symbol,
            raw=sorted(facts["explicit_symbols"]),
            source="untraceable",
            warnings=[
                f"Prompt contains explicit symbol(s) {sorted(facts['explicit_symbols'])}, "
                f"but tool requested {upper_symbol}."
            ],
        )

    if _has_bare_000001_without_disambiguation(prompt, facts):
        if upper_symbol in {"000001.SZ", "000001.SH"}:
            return _symbol_decision(
                "clarify",
                "ambiguous_000001_requires_confirmation",
                "rule_c_ambiguous_000001",
                tool_symbol,
                raw=["000001"],
                source="ambiguous",
                normalized_symbol=upper_symbol,
                warnings=["000001 may mean 000001.SZ Ping An Bank or 000001.SH Shanghai Composite."],
            )

    chinese_hits = facts["chinese_name_hits"]
    if chinese_hits and _looks_like_standard_symbol(upper_symbol):
        return _symbol_decision(
            "clarify",
            "chinese_name_requires_confirmation",
            "rule_d_chinese_name",
            tool_symbol,
            raw=chinese_hits,
            source="chinese_name",
            normalized_symbol=upper_symbol,
            warnings=["Chinese-name resolution requires audited confirmation in the MVP."],
        )

    for raw in facts["bare_candidates"]:
        normalized = normalize_symbol(raw)
        if (
            normalized.normalized_symbol
            and normalized.normalized_symbol.upper() == upper_symbol
            and not normalized.needs_confirmation
        ):
            return _symbol_decision(
                "allow",
                "safe_bare_symbol_mapping",
                "rule_b_safe_bare_symbol",
                tool_symbol,
                raw=[raw],
                source="normalizer",
                normalized_symbol=normalized.normalized_symbol,
                warnings=[
                    f"Pre-tool inferred mapping {raw} -> {normalized.normalized_symbol}; "
                    "record for audit."
                ],
            )

    return _symbol_decision(
        "block",
        "tool_symbol_not_traceable_to_user_prompt",
        "rule_f_untraceable_symbol",
        tool_symbol,
        raw=facts["bare_candidates"] + facts["chinese_name_hits"],
        source="untraceable",
        normalized_symbol=upper_symbol,
        warnings=[f"Tool symbol {upper_symbol} was not traceable to the original prompt."],
    )


def _extract_tool_symbols(tool_args: dict) -> list[str]:
    if not isinstance(tool_args, dict):
        return []
    symbols: list[str] = []
    for key in _SYMBOL_KEYS:
        if key not in tool_args:
            continue
        value = tool_args.get(key)
        if isinstance(value, str):
            symbols.extend(part.strip() for part in value.split(","))
        elif isinstance(value, (list, tuple, set)):
            symbols.extend(str(item).strip() for item in value)
        elif value is not None:
            symbols.append(str(value).strip())
    return _unique([symbol.upper() for symbol in symbols if symbol])


def _extract_prompt_facts(prompt: str) -> dict[str, Any]:
    upper = prompt.upper()
    explicit = set(re.findall(r"\b(?:\d{6}\.(?:SH|SZ|BJ)|\d{1,5}\.HK|[A-Z]{1,5}\.US)\b", upper))
    bare_numeric = re.findall(r"(?<![\w.])\d{4,6}(?![\w.])", upper)
    bare_letters = re.findall(r"(?<![\w.])[A-Z]{1,5}(?![\w.])", upper)
    bare_letters = [token for token in bare_letters if token not in {"SH", "SZ", "HK", "US"}]
    chinese_hits = [name for name in _CHINESE_NAME_KEYWORDS if name in prompt]
    bare_candidates = [token for token in bare_numeric + bare_letters if not _is_part_of_explicit(token, explicit)]
    return {
        "explicit_symbols": explicit,
        "bare_candidates": _unique(bare_candidates),
        "chinese_name_hits": chinese_hits,
        "upper_prompt": upper,
    }


def _has_bare_000001_without_disambiguation(prompt: str, facts: dict[str, Any]) -> bool:
    if "000001" not in facts["bare_candidates"]:
        return False
    upper = facts["upper_prompt"]
    if any(hint in prompt or hint in upper for hint in _AMBIGUOUS_000001_HINTS):
        return False
    return True


def _looks_like_standard_symbol(value: str) -> bool:
    return bool(re.fullmatch(r"(?:\d{6}\.(?:SH|SZ|BJ)|\d{1,5}\.HK|[A-Z]{1,5}\.US)", value))


def _is_part_of_explicit(token: str, explicit_symbols: set[str]) -> bool:
    return any(token in symbol.split(".") for symbol in explicit_symbols)


def _symbol_decision(
    decision: str,
    reason: str,
    matched_rule: str,
    tool_symbol: str,
    *,
    raw: list[str],
    source: str,
    normalized_symbol: str | None = None,
    warnings: list[str] | None = None,
) -> dict:
    return {
        "decision": decision,
        "reason": reason,
        "matched_rule": matched_rule,
        "tool_name": _SUPPORTED_TOOL,
        "tool_symbol": tool_symbol.upper(),
        "raw_symbol_candidates": _unique(raw),
        "warnings": warnings or [],
        "metadata": {
            "source": source,
            "normalized_symbol": normalized_symbol,
            "raw_input": raw[0] if raw else None,
        },
    }


def _decision(
    decision: str,
    reason: str,
    matched_rule: str,
    *,
    tool_name: str,
    tool_symbol: str | None,
    raw_symbol_candidates: list[str],
    warnings: list[str],
    metadata: dict[str, Any],
    details: list[dict],
) -> dict:
    return {
        "decision": decision,
        "reason": reason,
        "matched_rule": matched_rule,
        "tool_name": tool_name,
        "tool_symbol": tool_symbol,
        "raw_symbol_candidates": raw_symbol_candidates,
        "warnings": warnings,
        "metadata": metadata,
        "details": details,
    }


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
