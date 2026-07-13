"""Read-only financial-statements tool: three statements + key indicators.

Pulls a single stock's balance sheet, income statement, cash-flow statement, or
key per-period indicators from a market-appropriate public source:

* **A-share** (``.SH`` / ``.SZ`` / ``.BJ``) — Eastmoney's A-share F10 report
  datasets (``RPT_F10_FINANCE_*``), filtered on the dotted ``SECUCODE`` (e.g.
  ``600519.SH``). The legacy Sina ``quotes.sina.cn`` company-finance openapi
  returned a graceful-empty masking an upstream failure, so the A-share path now
  shares the Eastmoney transport with HK.
* **US** (``.US``) — SEC EDGAR companyfacts XBRL, resolved by ticker->CIK.
* **Hong Kong** (``.HK``) — Eastmoney's HK F10 financial-report datasets,
  filtered on the bare ``SECURITY_CODE``; ``indicators`` reads the
  main-indicator dataset.

Eastmoney requests go through :func:`backtest.loaders.eastmoney_client.get_json`
(``host_key="eastmoney"``); SEC requests go through the shared EDGAR client
(``host_key="sec"``).

The tool is read-only and self-contained: ``execute`` returns a JSON-string
envelope and never raises for a recoverable per-request failure — a bad symbol
or a transient HTTP error is reported inside the envelope.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backtest.loaders.eastmoney_client import get_json, resolve_secid
from backtest.loaders.sec_edgar_client import cik_for, get_company_facts
from src.adapters.a_stock_data.financials import (
    fetch_a_stock_financials,
    is_a_stock_financials_fallback_eligible,
    should_try_a_stock_financials_fallback,
)
from src.adapters.a_stock_data.normalizer import normalize_a_stock_financials_result
from src.agent.tools import BaseTool
from src.agent.tool_execution import ToolExecutionResult
from src.symbols.config import is_a_stock_data_adapter_enabled

logger = logging.getLogger(__name__)

# --- Eastmoney datacenter report API --------------------------------------

# Eastmoney datacenter report API. The three statements and the main-indicator
# dataset are addressed by report name, which differs by market (A / HK).
_EM_REPORT_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

# (market_prefix_group, statement) -> Eastmoney report name. ``a`` covers the
# mainland exchanges (markets 0/1); ``hk`` covers 116.
_EM_REPORT_NAME: dict[str, dict[str, str]] = {
    "a": {
        "balance": "RPT_F10_FINANCE_GBALANCE",
        "income": "RPT_F10_FINANCE_GINCOME",
        "cashflow": "RPT_F10_FINANCE_GCASHFLOW",
        "indicators": "RPT_F10_FINANCE_MAINFINADATA",
    },
    "hk": {
        "balance": "RPT_HKF10_FN_BALANCE",
        "income": "RPT_HKF10_FN_INCOME",
        "cashflow": "RPT_HKF10_FN_CASHFLOW",
        "indicators": "RPT_HKF10_FN_GMAININDICATOR",
    },
}

# Eastmoney mainland A-share markets (SZ/BJ = 0, SH = 1) and the HK market.
_EM_A_MARKETS = ("0", "1")
_EM_HK_MARKET = "116"

_SEC_CONCEPTS: dict[str, tuple[str, ...]] = {
    "balance": (
        "Assets",
        "AssetsCurrent",
        "CashAndCashEquivalentsAtCarryingValue",
        "Liabilities",
        "LiabilitiesCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent",
        "StockholdersEquity",
    ),
    "income": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "GrossProfit",
        "OperatingIncomeLoss",
        "NetIncomeLoss",
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted",
    ),
    "cashflow": (
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInFinancingActivities",
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
    ),
    "indicators": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "NetIncomeLoss",
        "Assets",
        "Liabilities",
        "StockholdersEquity",
        "EarningsPerShareDiluted",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ),
}

# --- Shared limits / validation ------------------------------------------

_VALID_STATEMENTS = ("balance", "income", "cashflow", "indicators")
_VALID_PERIODS = ("annual", "quarter")

# Defensive caps so a payload can never blow up the LLM context.
_MAX_PERIODS = 40
_MAX_FIELDS_PER_PERIOD = 200


def _error(message: str) -> str:
    """Build the failure envelope as a JSON string.

    Args:
        message: Human-readable error description.

    Returns:
        A ``{"ok": false, "error": ...}`` JSON string.
    """
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _truncate_period(record: dict[str, Any]) -> dict[str, Any]:
    """Cap one period's field count so a single record stays context-safe.

    Args:
        record: A flat period dict (field name -> value).

    Returns:
        A new dict with at most :data:`_MAX_FIELDS_PER_PERIOD` items, preserving
        insertion order. The original is never mutated.
    """
    items = list(record.items())
    if len(items) <= _MAX_FIELDS_PER_PERIOD:
        return dict(items)
    return dict(items[:_MAX_FIELDS_PER_PERIOD])


def _cap_periods(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the most recent periods, each truncated to a safe field count.

    Args:
        periods: Period records as returned by the provider parser.

    Returns:
        A new list of at most :data:`_MAX_PERIODS` field-capped records.
    """
    capped = periods[:_MAX_PERIODS]
    return [_truncate_period(record) for record in capped]


def _eastmoney_market_group(secid: str) -> str | None:
    """Classify an Eastmoney secid into the ``a`` or ``hk`` report group.

    Args:
        secid: Eastmoney secid (e.g. ``"1.600519"`` or ``"116.00700"``).

    Returns:
        ``"a"``, ``"hk"``, or ``None`` when the market prefix is unrecognized.
    """
    market = secid.split(".", 1)[0]
    if market in _EM_A_MARKETS:
        return "a"
    if market == _EM_HK_MARKET:
        return "hk"
    return None


def _parse_eastmoney_periods(payload: Any) -> list[dict[str, Any]]:
    """Extract period records from an Eastmoney datacenter report payload.

    Eastmoney nests report rows under ``result.data`` as a list of flat dicts.
    Any other shape yields an empty list rather than raising.

    Args:
        payload: Decoded JSON from the datacenter report API.

    Returns:
        A list of flat period dicts (possibly empty).
    """
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _eastmoney_filter(group: str, code: str, secid: str) -> str:
    """Build the datacenter ``filter`` clause for one market group.

    The A-share F10 datasets key on the dotted ``SECUCODE`` (e.g.
    ``600519.SH``), whereas the HK datasets key on the bare ``SECURITY_CODE``
    carried in the secid (e.g. ``00700``). No ``REPORT_TYPE`` clause
    is emitted: Eastmoney stores ``REPORT_TYPE`` as locale text (年报 / 一季报)
    or a ``2026/Q1`` string that differs by market and report, so a numeric
    filter matched zero rows. Period selection is done client-side instead
    (see :func:`_filter_by_period`).

    Args:
        group: Market group from :func:`_eastmoney_market_group`.
        code: Original Vibe-Trading symbol (e.g. ``"600519.SH"``).
        secid: Resolved Eastmoney secid (e.g. ``"1.600519"``).

    Returns:
        The Eastmoney ``filter`` query-parameter string.
    """
    if group == "a":
        return f'(SECUCODE="{code.upper()}")'
    bare_code = secid.split(".", 1)[1]
    return f'(SECURITY_CODE="{bare_code}")'


def _filter_by_period(
    periods: list[dict[str, Any]], period: str
) -> list[dict[str, Any]]:
    """Best-effort client-side period selection by report date.

    Eastmoney returns a mixed newest-first series (annual + interim reports).
    For ``annual`` we keep only fiscal-year-end rows (``REPORT_DATE`` ending
    ``-12-31``); if none match — e.g. an issuer whose fiscal year does not end
    in December — we fall back to the full series rather than drop all data.
    ``quarter`` returns the full newest-first series unchanged.

    Args:
        periods: Period records (newest-first) from the report parser.
        period: ``"annual"`` or ``"quarter"``.

    Returns:
        The filtered list; never empty when ``periods`` is non-empty.
    """
    if period != "annual":
        return periods
    annual = [
        row
        for row in periods
        if str(row.get("REPORT_DATE", ""))[:10].endswith("-12-31")
    ]
    return annual or periods


def _fetch_eastmoney_statement(
    code: str, *, statement: str, period: str
) -> dict[str, Any]:
    """Fetch one A-share/HK statement from Eastmoney, shaped into a result dict.

    Args:
        code: Symbol (e.g. ``"600519.SH"`` or ``"00700.HK"``).
        statement: One of :data:`_VALID_STATEMENTS`.
        period: ``"annual"`` or ``"quarter"``.

    Returns:
        ``{"periods": [...]}`` on success or ``{"error": ...}`` on failure;
        never raises.
    """
    secid = resolve_secid(code)
    if secid is None:
        return {"error": "unresolvable symbol"}

    group = _eastmoney_market_group(secid)
    if group is None:
        return {"error": "symbol is not an A-share or Hong Kong instrument"}

    params = {
        "reportName": _EM_REPORT_NAME[group][statement],
        "columns": "ALL",
        "filter": _eastmoney_filter(group, code, secid),
        "sortColumns": "REPORT_DATE",
        "sortTypes": "-1",
        "pageNumber": "1",
        "pageSize": str(_MAX_PERIODS),
        "source": "F10",
        "client": "PC",
    }
    try:
        payload = get_json(_EM_REPORT_URL, params=params)
    except Exception as exc:  # noqa: BLE001 - one bad fetch must not kill the call
        logger.warning("eastmoney statement fetch failed for %s: %s", code, exc)
        return {"error": str(exc)}

    periods = _filter_by_period(_parse_eastmoney_periods(payload), period)
    return {"periods": _cap_periods(periods)}


def _to_number(value: Any) -> float | None:
    """Coerce a numeric provider cell to float, preserving missing values."""
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick_sec_unit(units: dict[str, Any]) -> tuple[str, list[Any]]:
    """Pick the SEC XBRL unit bucket with the most reported rows."""
    best_key = ""
    best_rows: list[Any] = []
    for key, rows in units.items():
        if isinstance(rows, list) and len(rows) >= len(best_rows):
            best_key, best_rows = str(key), rows
    return best_key, best_rows


def _sec_period_matches(row: dict[str, Any], period: str) -> bool:
    """Return whether a SEC fact row belongs in the requested cadence."""
    if period != "annual":
        return True
    fp = str(row.get("fp") or "").upper()
    form = str(row.get("form") or "").upper()
    return fp == "FY" or form == "10-K"


def _fetch_sec_statement(code: str, *, statement: str, period: str) -> dict[str, Any]:
    """Fetch one US statement from SEC companyfacts, shaped as flat periods.

    Args:
        code: US symbol with ``.US`` suffix, e.g. ``"AAPL.US"``.
        statement: One of :data:`_VALID_STATEMENTS`.
        period: ``"annual"`` or ``"quarter"``.

    Returns:
        ``{"periods": [...]}`` on success or ``{"error": ...}`` on failure.
    """
    ticker = code.rsplit(".", 1)[0].strip().upper()
    try:
        cik = cik_for(ticker)
    except Exception as exc:  # noqa: BLE001 - surface provider failures as envelope
        logger.warning("SEC ticker lookup failed for %s: %s", code, exc)
        return {"error": f"SEC ticker lookup failed: {exc}"}
    if not cik:
        return {"error": "ticker not found in SEC company table"}

    try:
        facts = get_company_facts(cik)
    except Exception as exc:  # noqa: BLE001 - one bad fetch must not kill the call
        logger.warning("SEC companyfacts fetch failed for %s: %s", code, exc)
        return {"error": f"SEC companyfacts request failed: {exc}"}

    gaap = (facts.get("facts") or {}).get("us-gaap") if isinstance(facts, dict) else None
    if not isinstance(gaap, dict):
        return {"periods": []}

    periods_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for concept_name in _SEC_CONCEPTS[statement]:
        concept = gaap.get(concept_name)
        units = concept.get("units") if isinstance(concept, dict) else None
        if not isinstance(units, dict):
            continue
        unit_key, rows = _pick_sec_unit(units)
        for row in rows:
            if not isinstance(row, dict) or not _sec_period_matches(row, period):
                continue
            end = row.get("end")
            value = _to_number(row.get("val"))
            if not end or value is None:
                continue
            key = (end, row.get("fy"), row.get("fp"), row.get("form"), row.get("accn"))
            period_row = periods_by_key.setdefault(
                key,
                {
                    "REPORT_DATE": end,
                    "FISCAL_YEAR": row.get("fy"),
                    "FISCAL_PERIOD": row.get("fp"),
                    "FORM": row.get("form"),
                    "ACCESSION": row.get("accn"),
                    "_units": {},
                },
            )
            period_row[concept_name] = value
            period_row["_units"][concept_name] = unit_key

    periods = sorted(
        periods_by_key.values(),
        key=lambda row: str(row.get("REPORT_DATE") or ""),
        reverse=True,
    )
    return {"periods": _cap_periods(periods)}


def _classify_market(code: str) -> str | None:
    """Classify a symbol's suffix into ``a_share``, ``us``, ``hk``, or ``None``.

    Args:
        code: Symbol with a market suffix (e.g. ``"600519.SH"``, ``"AAPL.US"``).

    Returns:
        The market label, or ``None`` when the suffix is unrecognized.
    """
    suffix = code.rpartition(".")[2].strip().upper()
    if suffix in ("SH", "SZ", "BJ"):
        return "a_share"
    if suffix == "US":
        return "us"
    if suffix == "HK":
        return "hk"
    return None


def _with_a_stock_fallback_audit(
    fallback_result: dict[str, Any],
    *,
    code: str,
    statement: str,
    period: str,
    primary_envelope: dict[str, Any],
) -> dict[str, Any]:
    """Add financial fallback audit metadata to a normalized result."""

    fallback_result["market"] = "a_share"
    fallback_result["statement"] = statement
    fallback_result["period"] = period
    fallback_result.setdefault("fallback", {})["primary"] = {
        "source": primary_envelope.get("source"),
        "ok": primary_envelope.get("ok"),
        "error": primary_envelope.get("error"),
    }
    quality = fallback_result.get("_data_quality")
    if isinstance(quality, dict):
        meta = quality.get(code)
        if isinstance(meta, dict):
            warnings = meta.setdefault("warnings", [])
            for warning in (
                "primary_financials_unavailable",
                "a_stock_data_fallback_used",
            ):
                if warning not in warnings:
                    warnings.append(warning)
            meta["primary_source"] = primary_envelope.get("source")
            meta["primary_status"] = "ok" if primary_envelope.get("ok") else "failed_or_missing"
            meta["primary_error"] = primary_envelope.get("error")
            if not fallback_result.get("ok"):
                fallback_warnings = (
                    "a_stock_data_fallback_failed",
                )
                for warning in fallback_warnings:
                    if warning not in warnings:
                        warnings.append(warning)
    return fallback_result


def _append_fallback_not_eligible(
    envelope: dict[str, Any],
    *,
    code: str,
    eligibility: dict[str, Any],
) -> dict[str, Any]:
    """Attach an audit warning when fallback is intentionally refused."""

    warnings = envelope.setdefault("warnings", [])
    for warning in ("a_stock_data_fallback_not_eligible", str(eligibility.get("reason") or "")):
        if warning and warning not in warnings:
            warnings.append(warning)
    envelope.setdefault("fallback", {})["a_stock_data"] = {
        "attempted": False,
        "reason": eligibility.get("reason"),
        "symbol": code,
        "market": eligibility.get("market"),
        "asset_type": eligibility.get("asset_type"),
    }
    return envelope


_SENSITIVE_ERROR_QUERY_RE = re.compile(
    r"([?&](?:api[_-]?key|token|secret|authorization|password)=)[^&\s]+",
    re.IGNORECASE,
)
_SENSITIVE_ERROR_HEADER_RE = re.compile(
    r"(authorization\s*[:=]\s*)(?:bearer\s+)?\S+", re.IGNORECASE
)
_SENSITIVE_ERROR_ENV_RE = re.compile(
    r"\b[A-Z][A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD)\s*=\s*\S+"
)
_EXECUTION_ERROR_LIMIT = 300


def _safe_execution_error(value: Any) -> str | None:
    """Return a bounded error suitable for execution metadata only."""

    if value in (None, ""):
        return None
    text = str(value).splitlines()[0].strip()
    text = _SENSITIVE_ERROR_QUERY_RE.sub(r"\1[redacted]", text)
    text = _SENSITIVE_ERROR_HEADER_RE.sub(r"\1[redacted]", text)
    text = _SENSITIVE_ERROR_ENV_RE.sub("[redacted]", text)
    if len(text) > _EXECUTION_ERROR_LIMIT:
        text = f"{text[:_EXECUTION_ERROR_LIMIT]}..."
    return text or None


def _a_share_execution_metadata(
    *,
    code: str,
    statement: str,
    provider: str | None,
    source: str | None,
    upstream: str | None,
    fallback_used: bool,
    primary_error: Any = None,
    provider_success: bool,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build explicit A-share execution facts without inspecting result rows."""

    safe_error = _safe_execution_error(primary_error)
    execution_warnings = list(dict.fromkeys(str(item) for item in (warnings or []) if item))
    return {
        "schema_version": "financial_execution_metadata.v1",
        "tool_name": "get_financial_statements",
        "symbol": code,
        "statement_type": statement,
        "provider": provider,
        "source": source,
        # Eastmoney's current primary envelope has no distinct upstream fact.
        "upstream": upstream,
        "fallback": {
            "used": fallback_used,
            "primary_provider": "eastmoney",
            "primary_error": safe_error,
        },
        "fallback_used": fallback_used,
        "primary_error": safe_error,
        "data_quality": {
            "provider_success": provider_success,
            "warnings": execution_warnings,
        },
        "warnings": execution_warnings,
    }


def _with_execution_metadata(
    legacy_result: str,
    metadata: dict[str, Any] | None,
) -> ToolExecutionResult:
    """Return isolated execution facts while leaving legacy JSON untouched."""

    return ToolExecutionResult(
        legacy_result=legacy_result,
        execution_metadata=metadata,
    )


class FinancialStatementsTool(BaseTool):
    """Fetch a stock's three financial statements or key per-period indicators."""

    name = "get_financial_statements"
    description = (
        "Fetch a single stock's financial statements: balance sheet, income "
        "statement, cash-flow statement, or key per-period indicators (margins, "
        "ROE, EPS, etc.). Markets: A-share (.SH/.SZ/.BJ), US (.US) and "
        "Hong Kong (.HK). US uses SEC EDGAR companyfacts; A-share and HK use "
        "Eastmoney. Reports come back newest-first as flat per-period rows. Use "
        'this to read fundamentals before building a valuation or screen. Example: '
        '{"code": "600519.SH", "statement": "income", "period": "annual"}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Single symbol with a market suffix, e.g. '600519.SH', "
                    "'000001.SZ', 'AAPL.US', or '00700.HK'."
                ),
            },
            "statement": {
                "type": "string",
                "enum": list(_VALID_STATEMENTS),
                "description": (
                    "Which report to fetch: 'balance' (balance sheet), 'income' "
                    "(income statement), 'cashflow' (cash-flow statement), or "
                    "'indicators' (key per-period indicators)."
                ),
                "default": "indicators",
            },
            "period": {
                "type": "string",
                "enum": list(_VALID_PERIODS),
                "description": (
                    "Reporting cadence: 'annual' (annual reports) or 'quarter' "
                    "(quarterly reports)."
                ),
                "default": "annual",
            },
        },
        "required": ["code"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Execute through the legacy string-only public tool interface."""

        return self.execute_with_metadata(**kwargs).legacy_result

    def execute_with_metadata(self, **kwargs: Any) -> ToolExecutionResult:
        """Validate inputs, dispatch by market, and return a JSON envelope.

        Args:
            **kwargs: ``code`` (str, required), ``statement`` (one of balance|
                income|cashflow|indicators, default 'indicators'), ``period``
                (annual|quarter, default 'annual').

        Returns:
            A JSON string ``{"ok": true, "market": str, "source": str,
            "statement": str, "period": str, "data": {...}}`` when the fetch
            yields data, ``{"ok": false, "error": ...}`` when validation fails,
            or the same envelope with ``ok: false`` plus a top-level ``error``
            when the per-market fetch failed for every requested code (so a
            nested fetch error is never masked by a top-level ``ok: true``).
        """
        code = kwargs.get("code")
        if not isinstance(code, str) or not code.strip():
            return _with_execution_metadata(
                _error("code must be a non-empty symbol string"), None
            )
        code = code.strip()

        statement = kwargs.get("statement", "indicators")
        if statement not in _VALID_STATEMENTS:
            return _with_execution_metadata(
                _error(f"statement must be one of {list(_VALID_STATEMENTS)}"), None
            )

        period = kwargs.get("period", "annual")
        if period not in _VALID_PERIODS:
            return _with_execution_metadata(
                _error(f"period must be one of {list(_VALID_PERIODS)}"), None
            )

        market = _classify_market(code)
        if market is None:
            return _with_execution_metadata(
                _error("code must carry a supported suffix: .SH/.SZ/.BJ, .US, or .HK"),
                None,
            )

        if market == "us":
            result = _fetch_sec_statement(code, statement=statement, period=period)
            source = "sec_edgar"
        else:
            result = _fetch_eastmoney_statement(
                code, statement=statement, period=period
            )
            source = "eastmoney"

        # The fetch failed for every requested code (here, the single ``code``)
        # iff its result carries an ``error``. Surface that as a top-level
        # ``ok: false`` so a nested failure is never masked by ``ok: true``.
        all_failed = "error" in result
        envelope: dict[str, Any] = {
            "ok": not all_failed,
            "market": market,
            "source": source,
            "statement": statement,
            "period": period,
            "data": {code: result},
        }
        if all_failed:
            envelope["error"] = result["error"]
        primary_legacy_result = json.dumps(envelope, ensure_ascii=False)
        primary_error = envelope.get("error")
        if not is_a_stock_data_adapter_enabled():
            if market != "a_share":
                return _with_execution_metadata(primary_legacy_result, None)
            if all_failed:
                return _with_execution_metadata(
                    primary_legacy_result,
                    _a_share_execution_metadata(
                        code=code,
                        statement=statement,
                        provider=None,
                        source=source,
                        upstream=None,
                        fallback_used=False,
                        primary_error=primary_error,
                        provider_success=False,
                        warnings=[
                            "primary_financials_unavailable",
                            "a_stock_data_fallback_disabled",
                        ],
                    ),
                )
            return _with_execution_metadata(
                primary_legacy_result,
                _a_share_execution_metadata(
                    code=code,
                    statement=statement,
                    provider="eastmoney",
                    source=source,
                    upstream=None,
                    fallback_used=False,
                    provider_success=True,
                ),
            )

        if not should_try_a_stock_financials_fallback(envelope):
            if market != "a_share":
                return _with_execution_metadata(primary_legacy_result, None)
            return _with_execution_metadata(
                primary_legacy_result,
                _a_share_execution_metadata(
                    code=code,
                    statement=statement,
                    provider="eastmoney",
                    source=source,
                    upstream=None,
                    fallback_used=False,
                    provider_success=True,
                ),
            )

        eligibility = is_a_stock_financials_fallback_eligible(code, market=market)
        if not eligibility.get("eligible"):
            ineligible_envelope = _append_fallback_not_eligible(
                envelope,
                code=code,
                eligibility=eligibility,
            )
            if market != "a_share":
                return _with_execution_metadata(
                    json.dumps(ineligible_envelope, ensure_ascii=False), None
                )
            return _with_execution_metadata(
                json.dumps(ineligible_envelope, ensure_ascii=False),
                _a_share_execution_metadata(
                    code=code,
                    statement=statement,
                    provider=None if all_failed else "eastmoney",
                    source=source,
                    upstream=None,
                    fallback_used=False,
                    primary_error=primary_error,
                    provider_success=not all_failed,
                    warnings=[
                        "a_stock_data_fallback_not_eligible",
                        str(eligibility.get("reason") or ""),
                    ],
                ),
            )

        try:
            raw_fallback = fetch_a_stock_financials(
                code,
                statement_type=statement,
                period=period,
            )
        except Exception as exc:  # noqa: BLE001 - fallback must never crash the tool
            logger.warning("a-stock-data financial fallback failed for %s: %s", code, exc)
            raw_fallback = {
                "ok": False,
                "error": f"a_stock_data_fallback_exception: {exc}",
                "data": [],
                "source": "a_stock_data",
                "upstream": "exception",
            }

        fallback = normalize_a_stock_financials_result(
            raw_fallback,
            code,
            source=raw_fallback.get("source") if isinstance(raw_fallback, dict) else None,
            upstream=raw_fallback.get("upstream") if isinstance(raw_fallback, dict) else None,
            statement_type=statement,
        )
        audited_fallback = _with_a_stock_fallback_audit(
            fallback,
            code=code,
            statement=statement,
            period=period,
            primary_envelope=envelope,
        )
        fallback_success = bool(audited_fallback.get("ok"))
        fallback_warnings = list(
            (audited_fallback.get("_data_quality") or {}).get(code, {}).get("warnings") or []
        )
        if not fallback_success:
            fallback_warnings.append("a_stock_data_fallback_failed")
        return _with_execution_metadata(
            json.dumps(audited_fallback, ensure_ascii=False),
            _a_share_execution_metadata(
                code=code,
                statement=statement,
                provider=audited_fallback.get("provider") if fallback_success else None,
                source=audited_fallback.get("source"),
                upstream=audited_fallback.get("upstream"),
                fallback_used=True,
                primary_error=primary_error,
                provider_success=fallback_success,
                warnings=fallback_warnings,
            ),
        )
