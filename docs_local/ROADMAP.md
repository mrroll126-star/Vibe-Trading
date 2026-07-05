# Local Roadmap

This file tracks the local long-term plan for maintaining a private research version of Vibe-Trading.

## Phase 0: Bootstrap Local Setup

Status: completed on 2026-07-05.

Goal: create a clean, auditable local base without changing upstream business logic.

Planned steps:

1. Clone the original upstream project from `HKUDS/Vibe-Trading`.
2. Create local branches:
   - `main`: keep aligned with upstream.
   - `dev`: long-term local integration branch.
   - `feature/bootstrap-local-setup`: today's initialization branch.
3. Create the `docs_local/` project management folder.
4. Read the project structure.
5. Attempt basic local deployment in a later step.
6. Produce a Tailscale access plan in a later step.
7. If there is enough time and usage budget later, add a US data source smoke test.

## Git Remote Strategy

Current state:

- `origin` points to `https://github.com/HKUDS/Vibe-Trading`.
- No personal GitHub fork has been configured yet.
- No push should be performed until the user creates a fork and confirms the target.

Recommended future state:

- `origin`: the user's personal fork.
- `upstream`: `https://github.com/HKUDS/Vibe-Trading`.

Suggested future commands after the fork exists:

```bash
git remote rename origin upstream
git remote add origin https://github.com/<your-github-user>/Vibe-Trading.git
git fetch --all
```

## Branch Model

- `main`: only sync from upstream.
- `dev`: long-term local integration.
- `feature/*`: one feature or setup task per branch.
- Backup tags: create a local tag before syncing upstream into local work.

## Phase 0 Result

Completed:

1. Environment setup and dependency installation.
2. Local backend/frontend run verification.
3. Architecture discovery and documentation.
4. API auth local setup.
5. Tailscale remote-access design, later deferred by user decision.
6. US data-source smoke test script.
7. DeepSeek provider verification.
8. Minimal native Agent research task.

See:

* `docs_local/PHASE_0_BOOTSTRAP_SUMMARY.md`
* `docs_local/TEST_REPORT.md`
* `docs_local/MINIMAL_RESEARCH_TASK.md`

## Phase 1 Plan

Status: proposed.

Recommended order:

1. Full US data-source smoke test with explicit `.US` symbols.
2. Symbol normalization design.
3. Custom provider plugin framework design.
4. `a-stock-data` adapter planning.
5. LLM router design.

See:

* `docs_local/PHASE_1_PLAN.md`
* `docs_local/NEXT_TASKS.md`
