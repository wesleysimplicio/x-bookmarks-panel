# Contributing

Thanks for considering a contribution. A few rules to keep the project simple and readable.

## Before opening a PR

1. **Open an issue first** for structural changes, new dependencies, or large-scope features. Small changes (typo, bug fix, edge case) can come directly as a PR.
2. **Read [DESIGN.md](DESIGN.md)** to understand what was intentionally left out. Proposals to add an ORM, a frontend framework, auth, or remote deploy will be closed (read, appreciated, but closed).
3. **Run it locally**: `./setup.sh`, confirm the panel boots at `http://localhost:8765`, and that `curl http://localhost:8765/api/healthz` returns `{"ok": true}`.

## Conventions

- **Python**: PEP 8, f-strings, `pathlib`, `from __future__ import annotations`, type hints where they help.
- **No ORM.** SQLite directly in `server/db.py`.
- **No frontend framework.** HTML + fetch in `index.html`.
- **Comments only when the "why" isn't obvious in the code.**
- **Idempotency** for anything that touches the OS.
- **Docs canon** (`README.md`, `CLAUDE.md`, `DESIGN.md`, `CONTRIBUTING.md`, `CHANGELOG.md`) are **English-only**. A Portuguese README mirror lives at `README.pt-BR.md`. Other translations are welcome as `<doc>.<lang>.md` siblings.
- **Commits** in English, imperative, short scope: `feat: add export csv endpoint`, `fix: escape backticks in terminal prompt`.

## Manual testing

The project doesn't ship an automated test suite yet. Minimum smoke test before a PR:

```bash
./stop.sh
rm -f data/bookmarks.db

./setup.sh
cp examples/sample-relatorio.html relatorio-bookmarks-x.html
curl -X POST http://localhost:8765/api/oportunidades/import
open http://localhost:8765

# Checks:
#   [ ] Panel opens and shows 2 cards
#   [ ] Search with "/" works
#   [ ] Priority/status/progress filters reduce the cards
#   [ ] Clicking "Claude Code" puts the prompt on the clipboard (paste ⌘V in any editor)
#   [ ] Clicking "+ New project" creates <repo>/<slug>/ and runs git init
#   [ ] Re-importing the HTML preserves panel-edited status/tipo_execucao/notas
```

## Project scope

**In**: local triage, simple UI, integration with Claude Code / Cowork / gh, launchd always-on, SQLite.

**Out**: multi-user, remote deploy, auth, cloud sync, mobile app, scraping x.com itself (use the official API or your own pipeline to produce the HTML).

## Security

If you find a vulnerability, **don't open a public issue**. Email the maintainer (see GitHub profile). Priorities:

- Prompt escaping in `osascript` / `pbcopy`.
- Path validation when creating project folders (prevent slug-driven path traversal).
- Any vector that enables RCE outside the expected single-user scenario.

## PR style

- One PR, one scope. If you find two bugs, send two PRs.
- The description explains the **why**, not only the what. Reference the issue.
- Before/after: for UI changes attach a screenshot or gif; for API changes show request/response.
- `CHANGELOG.md` gets a new line at the top of `[Unreleased]`.

Thanks again — a well-described PR is half the work.
