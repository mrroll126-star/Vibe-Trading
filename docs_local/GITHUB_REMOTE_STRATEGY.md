# GitHub Remote Strategy

## 1. Current Status

Date: 2026-07-09

Repository:

```text
/Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading
```

Current branch:

```text
feature/bootstrap-local-setup
```

Latest local commit:

```text
c45ae12 feat: add a-stock-data financial normalizer
```

Current remote:

```text
origin = https://github.com/HKUDS/Vibe-Trading
```

Default upstream project branch:

```text
main
```

Local branch tracking:

* `main` tracks `origin/main`.
* `feature/bootstrap-local-setup` does not currently track any remote branch.

Local commit status:

* `feature/bootstrap-local-setup` is 41 commits ahead of `origin/main`.
* Those Phase 1 commits currently exist only locally.

Ignored sensitive/runtime paths confirmed:

* `agent/.env`
* `agent/runs/`
* `agent/sessions/`
* `local_reports/`

GitHub CLI:

* `gh` was not found in the current shell path.
* This is not a blocker; fork and push can be done with normal Git commands after the user creates a fork.

## 2. Recommended Remote Model

Recommended long-term model:

```text
origin   = user's fork
upstream = HKUDS/Vibe-Trading
```

Reason:

* `upstream` stays clean for syncing original Vibe-Trading changes.
* `origin` becomes the user's own remote backup and collaboration target.
* Local feature branches can be pushed safely to the user's fork without attempting to push to HKUDS.

Recommended branch roles:

| Branch | Role |
| --- | --- |
| `main` | Track upstream original project. Avoid local feature work. |
| `dev` | Long-term local integration branch. |
| `feature/bootstrap-local-setup` | Current Phase 0/Phase 1 baseline branch. |
| future `feature/*` | One feature or design task per branch. |

## 3. User Fork Steps

The user should create a GitHub fork first:

1. Open the upstream project:
   `https://github.com/HKUDS/Vibe-Trading`
2. Click **Fork**.
3. Create the fork under the user's GitHub account.
4. Copy the fork URL, for example:

```text
https://github.com/<USER_NAME>/Vibe-Trading.git
```

Do not paste API keys, tokens, or `.env` content into GitHub.

## 4. Recommended Command Template

Run these only after the fork exists and the user confirms the fork URL.

```bash
cd /Users/jz-home/Documents/Codex/workspace/Projects/Investment/IVSM-001_VibeTrading/Vibe-Trading

git remote rename origin upstream
git remote add origin <USER_FORK_URL>
git remote -v
git push -u origin feature/bootstrap-local-setup
```

Example with a placeholder:

```bash
git remote add origin https://github.com/<USER_NAME>/Vibe-Trading.git
```

Do not run `git push` until the user confirms the fork URL.

## 5. Optional Safety Tag Before First Push

Before the first push, it is useful to tag the local Phase 1 baseline:

```bash
git tag phase1-local-baseline-2026-07-09 c45ae12
git push origin phase1-local-baseline-2026-07-09
```

This tag is optional. It creates an easy restore point for the local guardrail baseline.

## 6. Rollback / Recovery

If the remote rename is done incorrectly:

```bash
git remote -v
git remote remove origin
git remote rename upstream origin
```

If `origin` is accidentally set to the wrong fork:

```bash
git remote set-url origin <CORRECT_USER_FORK_URL>
git remote -v
```

If a push fails because the remote does not exist:

* Confirm the fork URL.
* Confirm GitHub authentication.
* Retry only after the remote URL is correct.

## 7. Sensitive File Rules

Never push:

* `agent/.env`
* API keys
* OAuth files
* token files
* `agent/runs/`
* `agent/sessions/`
* `local_reports/`
* cache files
* logs
* databases

Before every push, run:

```bash
git status --short
git status --ignored --short | grep -E "agent/.env|agent/runs|agent/sessions|local_reports" || true
git ls-files agent/.env agent/runs agent/sessions local_reports
```

Expected:

* `git status --short` should only show intended source/docs changes, or be clean.
* ignored runtime paths may appear with `!!`.
* `git ls-files ...` should print nothing for sensitive/runtime paths.

## 8. Recommendation

Next recommended action:

Create the user's GitHub fork, then update remotes so:

```text
origin   -> user's fork
upstream -> HKUDS/Vibe-Trading
```

Then push only:

```text
feature/bootstrap-local-setup
```

Do not open a PR yet. This branch is a local product baseline, not a contribution-ready upstream patch.

