# Changelog

Dates come from the git history. There is no release tag. `pyproject.toml` has said `version = "0.1.0"` since 97afe50 (2026-04-24), so the sections below are grouped by date, not by release.

## 2026-11-16

- Renamed the project from Bifrost to OrgBrain. The package, the CLI (`orgbrain`), the `ORGBRAIN_*` env vars, `orgbrain.yaml`, the database names and the `urn:orgbrain:` prefix all changed, and older entries below use the new names.
- Existing installs need three steps: `mv ~/.bifrost ~/.orgbrain`, rename `BIFROST_*` to `ORGBRAIN_*` in `.env` and `bifrost.yaml` to `orgbrain.yaml`, then `docker compose down -v` and re-extract, because stored URNs and the old volume's DB user keep the old name.

## 2026-11-10

- Compliance booleans on repo ownership became a generic `compliance_tags` list.
- Local-dev database defaults now agree across compose, `alembic.ini`, `.env.example` and the `orgbrain init` template. Alembic reads its URL from `.env`.
- The test fixtures create `orgbrain_test` when it is missing and refuse a database whose name lacks `test`.
- Added `make migrate`, `make test`, a checks-only setup path in CONTRIBUTING and a compose healthcheck user.
- Aligned `@eslint/js` with eslint 9 so a fresh `npm ci` installs.
- `claude login` became `claude auth login` in the docs, the bootstrap hints and the error messages, because the CLI has no top-level `login` command.
- Rewrote the README, added `docs/DECISIONS.md` and `docs/testing.md`, and moved the PRD, the TRD and the specs to `docs/archive/`.

## 2026-11-05

- Added `docs/roadmap.md`: a survey of 20 systems and 25 experiment cards.
- Trimmed `docs/archive/trd.md` to a cited pre-implementation plan. Added the "Task execution" section to `SECURITY.md`.

## 2026-10-19 to 2026-10-22

- Settings moved into `orgbrain.yaml` sections, with manifest providers `backstage`, `codeowners` and `generic_yaml`. The migration history was squashed into one baseline.
- Identity providers `none`, `header` and `oidc_jwt`, CSRF checks, `admin` and `member` roles and `bft_` API tokens.
- Per-key Fernet encryption for stored credentials, SSRF resolve-then-check for git URLs and authorization on SSE streams.
- Slack escalation without a model in the path. Extraction and research run `claude -p` under `dontAsk` with an explicit tool list.
- Startup rejects unknown `ORGBRAIN_` names. Mermaid SVG output is sanitised. Added a pyright gate script and the AcmeCo demo.

## 2026-04-05 to 2026-06-11, initial build

- The extraction pipeline, research chat with per-source agents, handover documents and the chat-to-task workflow.
- The skeptic pass, a fast path, follow-up planning, blast-radius research and scope deepening.
- The learning loop, request correlation IDs and an append-only `audit_log`.
