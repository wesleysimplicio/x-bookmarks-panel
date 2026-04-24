# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.0] — 2026-04-24

### Added
- Trilingual UI: English, Portuguese, and Spanish. Language picker in the header persists the choice in `localStorage`. Default is detected from `navigator.language` (falls back to English).
- `lang` query field on `POST /api/oportunidades/<id>/executar` body. Propagates to `executor.executar()` and drives the generated prompt and the scaffolded `README.md` / `CLAUDE.md` language. Accepted values: `en`, `pt`, `es`. Default: `pt` (preserves existing callers).

### Changed
- `executor.montar_prompt`, `executor.criar_projeto`, and `executor.executar` now accept a `lang` keyword. Strings live in `PROMPT_I18N` and `SCAFFOLD_I18N` dicts.
- `index.html` runs every user-facing string through an `I18N` dictionary + `t(key, params)` helper. Data fields (author, insight, suggested action, etc.) are never translated — they come from the source HTML as-is.

## [0.1.2] — 2026-04-24

### Changed
- `CLAUDE.md`, `DESIGN.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` are now English-only (documentation canon). Portuguese documentation is reserved for `README.pt-BR.md`.

## [0.1.1] — 2026-04-24

### Changed
- `README.md` is now the canonical English version (default landing on GitHub).
- The Portuguese copy moved to `README.pt-BR.md` with bidirectional top-of-file links.

## [0.1.0] — 2026-04-24

### Added
- Initial open-source release of the panel.
- Flask 3 backend with routes `/api/healthz`, `/api/stats`, `/api/oportunidades`, `/api/oportunidades/<id>/executar`, `/api/oportunidades/import`, `/api/projetos`.
- SQLite schema with three tables: `oportunidades`, `execucoes`, `projetos`. Idempotent migration.
- Single-page UI in vanilla HTML+CSS+JS: cards with priority/status/category, debounced text search, stacked filters, independent progress flags (instalado / aplicado / projeto iniciado).
- Claude×Cowork heuristic via keyword + category scoring, with manual override from UI or API.
- **+ New project** button creates `<repo>/<slug>/`, writes `README.md` + `CLAUDE.md`, runs `git init` and, if `gh` is authenticated, `gh repo create --private --push`.
- Idempotent importer: reads the `BOOKMARKS` array from `relatorio-bookmarks-x.html`, preserves panel-edited fields.
- macOS scripts: idempotent `setup.sh`, `install-launchd.sh` with plist templates, `healthcheck.sh` watchdog every 5 min, `start.sh` / `stop.sh`.
- Configuration via `.env` (port, host, label prefix, Cowork app, alternate HTML path).
- Example at `examples/sample-relatorio.html` with synthetic data.
- Documentation: `README.md`, `CLAUDE.md`, `DESIGN.md`, `CONTRIBUTING.md`.
- `.gitignore` blocking user data (DB, triage HTML, logs, `.env`, `.venv`, captures, profile analyses, generated folders).

[Unreleased]: https://github.com/wesleysimplicio/x-bookmarks-panel/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/wesleysimplicio/x-bookmarks-panel/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/wesleysimplicio/x-bookmarks-panel/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/wesleysimplicio/x-bookmarks-panel/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/wesleysimplicio/x-bookmarks-panel/releases/tag/v0.1.0
