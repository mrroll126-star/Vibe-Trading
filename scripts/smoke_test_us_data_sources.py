#!/usr/bin/env python3
"""Smoke test US-equity data loaders without changing provider logic.

The script calls each existing Vibe-Trading loader directly, records what
happened, and writes local-only Markdown/JSON reports under ``local_reports/``.
It is intentionally diagnostic: missing API keys are skipped, unsupported data
types are recorded as unsupported, and provider failures do not abort the run.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from backtest.loaders.registry import LOADER_REGISTRY, _ensure_registered  # noqa: E402


DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ"]
DEFAULT_PROVIDERS = [
    "yahoo",
    "stooq",
    "sina",
    "eastmoney",
    "yfinance",
    "tiingo",
    "fmp",
    "finnhub",
    "alphavantage",
    "akshare",
    "local",
]

API_KEY_ENVS = {
    "tiingo": "TIINGO_API_KEY",
    "fmp": "FMP_API_KEY",
    "finnhub": "FINNHUB_API_KEY",
    "alphavantage": "ALPHAVANTAGE_API_KEY",
}

PLACEHOLDER_KEYS = {
    "",
    "changeme",
    "replace_with_key",
    "replace_with_strong_random_key",
    "your_api_key",
    "your_tiingo_api_key",
    "your-alphavantage-api-key",
    "demo",
    "xxx",
}

DAILY_TESTS = {
    "daily_1mo": 30,
    "daily_1y": 365,
    "daily_5y": 365 * 5,
}

EXTENDED_UNSUPPORTED_TESTS = [
    "intraday_minute_bars",
    "fundamentals",
    "earnings_financials",
    "options_chain",
]


@dataclass
class SmokeResult:
    market: str
    provider: str
    symbol: str
    normalized_symbol: str
    test_type: str
    status: str
    elapsed_ms: int
    rows_count: int
    returned_fields: list[str]
    requires_api_key: bool
    error_type: str
    error_summary: str
    timestamp: str


class TimeoutExpired(Exception):
    """Raised when one provider call exceeds the configured timeout."""


@contextlib.contextmanager
def time_limit(seconds: float):
    """Limit one provider call on POSIX systems."""
    if seconds <= 0 or not hasattr(signal, "setitimer"):
        yield
        return

    def _handle_timeout(_signum: int, _frame: Any) -> None:
        raise TimeoutExpired(f"provider call exceeded {seconds:g}s timeout")

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, _handle_timeout)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def normalize_us_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned:
        return cleaned
    if cleaned.startswith("LOCAL:"):
        inner = cleaned.split(":", 1)[1]
        return f"local:{normalize_us_symbol(inner)}"
    if "." in cleaned:
        return cleaned
    return f"{cleaned}.US"


def has_real_key(provider: str) -> bool:
    env_name = API_KEY_ENVS.get(provider)
    if not env_name:
        return True
    value = os.getenv(env_name, "").strip()
    return value.lower() not in PLACEHOLDER_KEYS


def summarize_error(exc: BaseException) -> tuple[str, str]:
    message = str(exc).replace("\n", " ").strip()
    if len(message) > 240:
        message = message[:237] + "..."
    return type(exc).__name__, message


def make_result(
    *,
    provider: str,
    symbol: str,
    normalized_symbol: str,
    test_type: str,
    status: str,
    elapsed_ms: int = 0,
    rows_count: int = 0,
    returned_fields: Iterable[str] | None = None,
    requires_api_key: bool = False,
    error_type: str = "",
    error_summary: str = "",
) -> SmokeResult:
    return SmokeResult(
        market="us_equity",
        provider=provider,
        symbol=symbol,
        normalized_symbol=normalized_symbol,
        test_type=test_type,
        status=status,
        elapsed_ms=elapsed_ms,
        rows_count=rows_count,
        returned_fields=sorted(list(returned_fields or [])),
        requires_api_key=requires_api_key,
        error_type=error_type,
        error_summary=error_summary,
        timestamp=utc_now(),
    )


def unsupported_result(
    provider: str,
    symbol: str,
    normalized_symbol: str,
    test_type: str,
    requires_api_key: bool,
) -> SmokeResult:
    return make_result(
        provider=provider,
        symbol=symbol,
        normalized_symbol=normalized_symbol,
        test_type=test_type,
        status="unsupported",
        requires_api_key=requires_api_key,
        error_type="UnsupportedByLoaderInterface",
        error_summary="Existing loader interface exposes OHLCV history only for this provider.",
    )


def instantiate_loader(provider: str) -> tuple[Any | None, str]:
    loader_cls = LOADER_REGISTRY.get(provider)
    if loader_cls is None:
        return None, "Provider is not registered in LOADER_REGISTRY."
    try:
        return loader_cls(), ""
    except Exception as exc:  # noqa: BLE001 - diagnostic script must continue
        error_type, summary = summarize_error(exc)
        return None, f"{error_type}: {summary}"


def run_daily_test(
    provider: str,
    loader: Any,
    symbol: str,
    normalized_symbol: str,
    test_type: str,
    days_back: int,
    timeout: float,
    requires_api_key: bool,
) -> SmokeResult:
    end = date.today()
    start = end - timedelta(days=days_back)
    started = time.perf_counter()
    try:
        with time_limit(timeout):
            data = loader.fetch(
                [normalized_symbol],
                start.isoformat(),
                end.isoformat(),
                interval="1D",
            )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        frame = data.get(normalized_symbol) if isinstance(data, dict) else None
        if frame is None and isinstance(data, dict) and data:
            frame = next(iter(data.values()))
        if frame is None or getattr(frame, "empty", True):
            return make_result(
                provider=provider,
                symbol=symbol,
                normalized_symbol=normalized_symbol,
                test_type=test_type,
                status="failed",
                elapsed_ms=elapsed_ms,
                requires_api_key=requires_api_key,
                error_type="EmptyResult",
                error_summary="Provider returned no rows for the requested window.",
            )
        fields = [str(column) for column in getattr(frame, "columns", [])]
        return make_result(
            provider=provider,
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            test_type=test_type,
            status="success",
            elapsed_ms=elapsed_ms,
            rows_count=int(len(frame)),
            returned_fields=fields,
            requires_api_key=requires_api_key,
        )
    except Exception as exc:  # noqa: BLE001 - every row should become a report record
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        error_type, summary = summarize_error(exc)
        return make_result(
            provider=provider,
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            test_type=test_type,
            status="failed",
            elapsed_ms=elapsed_ms,
            requires_api_key=requires_api_key,
            error_type=error_type,
            error_summary=summary,
        )


def run_provider_symbol(
    provider: str,
    symbol: str,
    quick: bool,
    timeout: float,
) -> list[SmokeResult]:
    normalized_symbol = normalize_us_symbol(symbol)
    requires_api_key = provider in API_KEY_ENVS

    results = [
        unsupported_result(
            provider,
            symbol,
            normalized_symbol,
            "quote_latest_price",
            requires_api_key,
        )
    ]

    if not quick:
        results.extend(
            unsupported_result(provider, symbol, normalized_symbol, test_type, requires_api_key)
            for test_type in EXTENDED_UNSUPPORTED_TESTS
        )

    loader, init_error = instantiate_loader(provider)
    if loader is None:
        for test_type in selected_daily_tests(quick):
            results.append(
                make_result(
                    provider=provider,
                    symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    test_type=test_type,
                    status="unsupported",
                    requires_api_key=requires_api_key,
                    error_type="LoaderUnavailable",
                    error_summary=init_error,
                )
            )
        return results

    if requires_api_key and not has_real_key(provider):
        env_name = API_KEY_ENVS[provider]
        for test_type in selected_daily_tests(quick):
            results.append(
                make_result(
                    provider=provider,
                    symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    test_type=test_type,
                    status="skipped",
                    requires_api_key=True,
                    error_type="MissingApiKey",
                    error_summary=f"{env_name} is not set; provider intentionally skipped.",
                )
            )
        return results

    try:
        available = bool(loader.is_available())
    except Exception as exc:  # noqa: BLE001 - keep the report going
        error_type, summary = summarize_error(exc)
        for test_type in selected_daily_tests(quick):
            results.append(
                make_result(
                    provider=provider,
                    symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    test_type=test_type,
                    status="failed",
                    requires_api_key=requires_api_key,
                    error_type=error_type,
                    error_summary=f"is_available failed: {summary}",
                )
            )
        return results

    if not available:
        reason = "Provider reported unavailable."
        if provider == "local":
            reason = (
                "Local Data Bridge config was not found or has no sources at "
                "~/.vibe-trading/data-bridge/config.yaml."
            )
        for test_type in selected_daily_tests(quick):
            results.append(
                make_result(
                    provider=provider,
                    symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    test_type=test_type,
                    status="skipped",
                    requires_api_key=requires_api_key,
                    error_type="ProviderUnavailable",
                    error_summary=reason,
                )
            )
        return results

    for test_type, days_back in selected_daily_tests(quick).items():
        results.append(
            run_daily_test(
                provider,
                loader,
                symbol,
                normalized_symbol,
                test_type,
                days_back,
                timeout,
                requires_api_key,
            )
        )
    return results


def selected_daily_tests(quick: bool) -> dict[str, int]:
    if quick:
        return {"daily_1mo": DAILY_TESTS["daily_1mo"]}
    return dict(DAILY_TESTS)


def build_summary(results: list[SmokeResult]) -> dict[str, Any]:
    status_counts = Counter(result.status for result in results)
    provider_counts: dict[str, Counter[str]] = defaultdict(Counter)
    provider_elapsed_success: dict[str, list[int]] = defaultdict(list)
    for result in results:
        provider_counts[result.provider][result.status] += 1
        if result.status == "success":
            provider_elapsed_success[result.provider].append(result.elapsed_ms)
    by_provider = {}
    for provider in sorted(provider_counts):
        counts = dict(provider_counts[provider])
        elapsed = provider_elapsed_success.get(provider, [])
        counts["avg_success_elapsed_ms"] = int(sum(elapsed) / len(elapsed)) if elapsed else None
        by_provider[provider] = counts
    return {
        "total_records": len(results),
        "status_counts": dict(status_counts),
        "by_provider": by_provider,
    }


def write_json_report(path: Path, metadata: dict[str, Any], results: list[SmokeResult]) -> None:
    payload = {
        "metadata": metadata,
        "summary": build_summary(results),
        "results": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown_report(path: Path, metadata: dict[str, Any], results: list[SmokeResult]) -> None:
    summary = build_summary(results)
    lines = [
        "# US Data Source Smoke Test Report",
        "",
        f"* Generated at: `{metadata['generated_at']}`",
        f"* Quick mode: `{metadata['quick']}`",
        f"* Timeout per provider call: `{metadata['timeout_seconds']}s`",
        f"* Symbols: `{', '.join(metadata['symbols'])}`",
        f"* Providers: `{', '.join(metadata['providers'])}`",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| -- | --: |",
    ]
    for status in ("success", "failed", "skipped", "unsupported"):
        lines.append(f"| {status} | {summary['status_counts'].get(status, 0)} |")

    lines.extend(
        [
            "",
            "## Provider Summary",
            "",
            "| Provider | Success | Failed | Skipped | Unsupported | Avg Success ms |",
            "| -- | --: | --: | --: | --: | --: |",
        ]
    )
    for provider, counts in summary["by_provider"].items():
        avg_ms = counts.get("avg_success_elapsed_ms")
        avg_text = "" if avg_ms is None else str(avg_ms)
        lines.append(
            "| {provider} | {success} | {failed} | {skipped} | {unsupported} | {avg} |".format(
                provider=provider,
                success=counts.get("success", 0),
                failed=counts.get("failed", 0),
                skipped=counts.get("skipped", 0),
                unsupported=counts.get("unsupported", 0),
                avg=avg_text,
            )
        )

    lines.extend(
        [
            "",
            "## Detail",
            "",
            "| Provider | Symbol | Test | Status | Rows | Fields | Elapsed ms | Error |",
            "| -- | -- | -- | -- | --: | -- | --: | -- |",
        ]
    )
    for result in results:
        fields = ", ".join(result.returned_fields)
        error = result.error_summary.replace("|", "\\|")
        lines.append(
            "| {provider} | {symbol} | {test_type} | {status} | {rows} | {fields} | {elapsed} | {error} |".format(
                provider=result.provider,
                symbol=result.normalized_symbol,
                test_type=result.test_type,
                status=result.status,
                rows=result.rows_count,
                fields=fields,
                elapsed=result.elapsed_ms,
                error=error,
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.replace(",", " ").split() if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run provider-by-provider US data source smoke tests."
    )
    parser.add_argument(
        "--symbols",
        default=" ".join(DEFAULT_SYMBOLS),
        help="Comma or space separated symbols. Bare US tickers are normalized to .US.",
    )
    parser.add_argument(
        "--providers",
        default=" ".join(DEFAULT_PROVIDERS),
        help="Comma or space separated provider names.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout in seconds for each provider fetch call.",
    )
    parser.add_argument(
        "--output-dir",
        default="local_reports",
        help="Directory for local-only JSON and Markdown reports.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use fewer symbols and only the 1-month daily history test.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _ensure_registered()

    symbols = parse_csv_arg(args.symbols)
    providers = parse_csv_arg(args.providers)
    if args.quick:
        symbols = symbols[:2]

    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[SmokeResult] = []
    for provider in providers:
        for symbol in symbols:
            results.extend(run_provider_symbol(provider, symbol, args.quick, args.timeout))

    generated_at = utc_now()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    metadata = {
        "generated_at": generated_at,
        "repo": str(ROOT),
        "quick": bool(args.quick),
        "timeout_seconds": args.timeout,
        "symbols": symbols,
        "normalized_symbols": [normalize_us_symbol(symbol) for symbol in symbols],
        "providers": providers,
    }

    json_path = output_dir / f"us_data_sources_smoke_{timestamp}.json"
    markdown_path = output_dir / f"us_data_sources_smoke_{timestamp}.md"
    write_json_report(json_path, metadata, results)
    write_markdown_report(markdown_path, metadata, results)

    summary = build_summary(results)
    print("US data source smoke test complete.")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
