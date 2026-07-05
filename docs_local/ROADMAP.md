# Local Roadmap

This file tracks the local long-term plan for maintaining a private research version of Vibe-Trading.

## Today: Bootstrap Local Setup

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

## Near-Term Milestones

1. Environment setup and dependency installation.
2. Local backend/frontend run verification.
3. Architecture discovery and documentation.
4. Tailscale remote access design with authentication.
5. US data source smoke test.
