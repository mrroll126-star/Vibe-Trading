"""Rule-based guard for prompts that explicitly forbid estimated facts."""

from __future__ import annotations

import re
from typing import Any


NO_ESTIMATE_TERMS = [
    "不要估算",
    "不要推测",
    "不要猜",
    "不要编",
    "只使用实际获取到的数据",
    "只使用工具返回数据",
    "没有拿到就说没有",
    "不要补全",
    "不要根据历史推算",
    "do not estimate",
    "no estimates",
    "do not guess",
    "do not infer",
    "use only retrieved data",
    "use only tool-returned data",
    "if missing, say missing",
    "do not fabricate",
]

ESTIMATE_TERMS = [
    "估算",
    "约",
    "大概",
    "推算",
    "可能为",
    "estimated",
    "approximately",
    "approx.",
    "roughly",
    "around",
    "inferred",
]

MARKET_FACT_TERMS = [
    "价格",
    "最新价",
    "收盘价",
    "涨跌幅",
    "成交额",
    "成交量",
    "市值",
    "pe",
    "p/e",
    "eps",
    "股息率",
    "资金流",
    "净流入",
    "新闻",
    "研报",
    "target price",
    "price",
    "close",
    "volume",
    "turnover",
    "market cap",
    "fund flow",
]

_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?\s*(?:%|亿元|万元|元|股|手|亿|万|倍|shares|usd|rmb|cny)?", re.I)


def detect_no_estimate_request(prompt: str) -> dict[str, Any]:
    """Detect explicit instructions to use only retrieved/tool-returned facts."""

    text = (prompt or "").lower()
    matched_terms = [term for term in NO_ESTIMATE_TERMS if term.lower() in text]
    return {
        "enabled": bool(matched_terms),
        "matched_terms": matched_terms,
        "reason": "matched no-estimate terms" if matched_terms else "no no-estimate terms matched",
    }


def build_no_estimate_system_addendum(prompt: str) -> str:
    """Return an extra system instruction when the prompt forbids estimates."""

    detected = detect_no_estimate_request(prompt)
    if not detected["enabled"]:
        return ""
    return (
        "\n\n## No Estimate Guard\n"
        "- The user explicitly asked to avoid estimates, guesses, inferred facts, or fabricated market data.\n"
        "- Do not output estimated factual market numbers such as price, percent change, turnover, volume, market cap, PE, EPS, fund flow, news dates, or report dates.\n"
        "- A factual market number may be used only when it is returned directly by a tool (`tool_returned`) or can be audited from tool-returned fields (`computed_from_tool_data`).\n"
        "- If a field is missing, write `未获取到` / `unavailable` instead of filling it.\n"
        "- Keep interpretations separate from facts and label them as `interpretation`.\n"
    )


def find_estimated_market_fact_claims(report: str) -> list[str]:
    """Find lines that look like estimated factual market numbers.

    This is intentionally conservative and rule-based: it requires an estimate
    word, a numeric token, and a market-fact term in the same local segment.
    """

    claims: list[str] = []
    for segment in _segments(report):
        lowered = segment.lower()
        if not any(term.lower() in lowered for term in ESTIMATE_TERMS):
            continue
        if not _NUMBER_RE.search(segment):
            continue
        if not any(term.lower() in lowered for term in MARKET_FACT_TERMS):
            continue
        claims.append(segment.strip())
    return claims


def append_no_estimate_warning(report: str, prompt: str) -> str:
    """Append a mechanical warning when no-estimate prompts get estimated facts."""

    detected = detect_no_estimate_request(prompt)
    if not detected["enabled"]:
        return report
    claims = find_estimated_market_fact_claims(report)
    if not claims:
        return report

    lines = [
        report.rstrip(),
        "",
        "## No Estimate Warning",
        "",
        "- The user explicitly requested no estimates or guesses. The following estimated market-fact phrasing was detected mechanically and should not be treated as factual unless it is backed by tool-returned or auditable computed data:",
    ]
    for claim in claims[:10]:
        lines.append(f"- {claim}")
    if len(claims) > 10:
        lines.append(f"- ... {len(claims) - 10} additional estimated claim(s) omitted from this warning.")
    lines.append("- This warning is rule-based and does not rewrite the report body in the MVP.")
    return "\n".join(lines)


def _segments(report: str) -> list[str]:
    text = report or ""
    rough_segments = re.split(r"[\n。；;]", text)
    return [segment.strip() for segment in rough_segments if segment.strip()]
