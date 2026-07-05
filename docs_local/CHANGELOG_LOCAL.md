# Local Changelog

This changelog tracks local-only changes that are not part of upstream Vibe-Trading.

## 2026-07-05

### Added

- Cloned upstream `HKUDS/Vibe-Trading` into the local project workspace.
- Created local branch model:
  - `main`
  - `dev`
  - `feature/bootstrap-local-setup`
- Added `docs_local/` project management skeleton.

### Changed

- No upstream business code changed.

### Security

- No real `.env`, token, API key, OAuth file, cache, database, or log was created.
- No shell tools were enabled.
- No remote access was exposed.

### Git

- No commits created yet.
- No push performed.
- `origin` still points to upstream and should be changed after the user creates a fork.

## 2026-07-05 Read-Only Discovery Update

### Added

- Expanded `CURRENT_ARCHITECTURE.md` with runtime, entry points, data source layer, tool layer, API/security behavior, storage/cache locations, and known risks.
- Expanded `DATA_SOURCE_TEST_REPORT.md` with provider files, fallback chains, symbol formats, existing tests, and a future US smoke test proposal.
- Expanded `DEPLOYMENT_TAILSCALE.md` with a safe Tailnet-only access plan.
- Expanded `TEST_REPORT.md` with a next-round deployment plan, without running it.
- Updated `NEXT_TASKS.md` with the recommended next step.

### Changed

- Documentation only.

### Security

- No auth logic changed.
- No shell tools enabled.
- No `.env`, token, API key, OAuth file, cache, database, or log was created.
- No service was exposed.

## 2026-07-05 Basic Local Deployment

### Environment

- Installed Homebrew Python 3.11 because the machine only had system Python 3.9.6.
- Created project virtual environment at `.venv`.
- Installed backend dependencies with editable install.
- Installed frontend dependencies with npm.

### Validation

- Backend started successfully on `127.0.0.1:8899`.
- Frontend started successfully on `127.0.0.1:5899`.
- Verified backend health, API metadata, CLI help, frontend HTML, and local API access.
- Stopped both services after validation.

### Changed

- Documentation only.
- No `.gitignore` change was needed because `.venv/`, `node_modules/`, `agent/.env`, and `.env` were already ignored.

### Security

- No real `.env` was created.
- No token/API key/OAuth file was created.
- Shell tools were not enabled.
- Authentication logic was not changed.
- Services were bound only to `127.0.0.1` during testing.
