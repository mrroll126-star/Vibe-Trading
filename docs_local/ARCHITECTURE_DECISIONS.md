# Architecture Decisions

This file records local project boundaries. These decisions are meant to keep the project auditable, reversible, and easy to sync with upstream.

## ADR-001: Do Not Replace Existing Data Sources In Phase 1

Decision:
The first phase will only add adapters, providers, or test scripts. It will not delete, bypass, or replace the existing Vibe-Trading data source chain for A-share, US, or HK stocks.

Reason:
This keeps upstream compatibility, reduces breakage risk, and makes future upstream sync easier.

Boundary:
Unless the user explicitly approves it, do not delete, replace, or heavily refactor the original provider chain.

## ADR-002: Remote Access Must Use Authentication

Decision:
Any Tailscale, LAN, or non-localhost access must use `API_AUTH_KEY` or an equivalent project authentication mechanism.

Reason:
This is a financial research Agent project and may later involve local files, API keys, research data, and trading-related integrations.

Boundary:
Do not implement unauthenticated remote access.

## ADR-003: Shell Tools Are Disabled By Default

Decision:
`VIBE_TRADING_ENABLE_SHELL_TOOLS` or any equivalent shell-capable tools must remain disabled by default.

Reason:
Shell tools can execute commands on the local machine, which is risky in a remote access setup.

Boundary:
Do not enable shell tools by default in Docker Compose, sample environment files, or startup scripts. If they are ever needed, explain the risk and wait for explicit user approval.

## ADR-004: Sensitive Files Must Not Enter Git

Decision:
Do not commit `.env`, tokens, API keys, OAuth files, caches, databases, logs, local absolute path configuration, or generated private reports.

Boundary:
Check `.gitignore` before adding local artifacts. Sample files may use placeholders only.

## ADR-005: Long-Term Maintenance Uses Fork + Upstream + Dev + Feature Branches

Decision:
`main` tracks upstream. `dev` is the user's long-term integration branch. Each feature uses a separate `feature/*` branch.

Boundary:
Do not perform long-term local modifications directly on `main`.

## ADR-006: Do Not Integrate a-stock-data Today

Decision:
Today is only for bootstrap, documentation, discovery, and possibly a low-risk smoke test.

Boundary:
Do not directly integrate `simonlin1212/a-stock-data` into the core flow today.

## ADR-007: No Large Refactor Today

Decision:
Today should not include large-scale refactoring.

Boundary:
Keep changes small, documented, and reversible.

## ADR-008: LLM Must Not Invent Market Data

Decision:
LLM-generated research reports must not invent prices, volumes, turnover, dates, financial metrics, fund-flow numbers, announcements, news, or research-report facts. Factual market claims must be grounded in tool-returned data or explicitly marked as unavailable.

Reason:
Investment research is highly sensitive to data freshness and factual accuracy. Fabricated market data can make the product unusable or dangerous for short-term research.

Boundary:
If tool data is missing, stale, failed, delayed, ambiguous, or timestamp-unknown, the system must disclose that state instead of filling gaps with model guesses.

Implementation priority:
Freshness and anti-hallucination guardrails must be implemented before integrating `a-stock-data` into production research workflows.
