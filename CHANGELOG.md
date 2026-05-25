# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `exports/skills-items.csv` and `exports/skills-items.md`: dump of opportunities flagged with Claude/AI skills (23 items — links, author, category, priority, status, insight, suggested action).

## [0.4.0] - 2026-05-08

### Added
- `pyproject.toml` (hatchling) declaring distribution name `x-bookmarks-panel`, console-script `bookmarks-panel = "bookmarks_panel.app:main"`, and runtime dep `flask>=3.0`.
- `server/__init__.py` so the directory is recognized as a Python package; built wheel re-maps `server/` to import name `bookmarks_panel/` via `[tool.hatch.build.targets.wheel.sources]`.
- Runtime root resolution in `server/db.py` (`_resolve_root` + `_seed_static_assets`): respects `BOOKMARKS_ROOT`, falls back to repo root when running from source, and seeds `~/.x-bookmarks-panel/` (with bundled `index.html` + `examples/sample-relatorio.html`) when installed via pip.
- Distributed as a Python package on PyPI (`pip install x-bookmarks-panel`).

### Changed
- Bump VERSION 0.3.0 -> 0.4.0 (minor: PyPI distribution added).
- `server/app.py`, `server/importer.py`, `server/executor.py` switched from sibling `import db/importer/executor` to relative imports (`from . import db, executor, importer`, `from .db import ...`) so the package works under `python -m bookmarks_panel.app`.
- `start.sh` now runs `python -m bookmarks_panel.app` (was `cd server && python app.py`).
- `setup.sh` installs the package itself via `pip install -e .` (was `pip install -r server/requirements.txt`) and initializes the DB via `from bookmarks_panel import db, importer`.

## [0.3.0] - 2026-05-07

### Added
- Adopted `agentic-starter` scaffold: `AGENTS.md`, `CLAUDE.md`, `.specs/{product,architecture,workflow,sprints}/`, `.skills/`, `.claude/{settings.json,hooks/}`, `.codex/config.toml`, `.github/{workflows/dod.yml,PULL_REQUEST_TEMPLATE.md,ISSUE_TEMPLATE/,copilot-instructions.md}`, `playwright.config.ts`, `presentation/`.
- `VERSION` file as version source-of-truth.
- `.specs/product/{VISION,DOMAIN,PERSONAS}.md` mapped to oportunidade, execucao, projeto, tipo_execucao, prioridade.
- `.specs/architecture/{DESIGN,PATTERNS}.md` aligned with single-HTML/JS stack.
- `.specs/sprints/BACKLOG.md` from real TODOs.

### Changed
- Bump VERSION 0.2.0 -> 0.3.0 (minor: structure added).
- `AGENTS.md`/`CLAUDE.md`/`.github/copilot-instructions.md` aligned with real stack.

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
