# CLAUDE.md — Project context

Auto-loaded by Claude Code when a session starts at the repo root. Keeps context persistent between sessions.

## About

Local panel for triaging **x.com** bookmarks. Reads a curated HTML file (`relatorio-bookmarks-x.html`), persists everything in SQLite (`data/bookmarks.db`), and renders cards with an **Execute** button that fires either Claude Code or the Claude desktop app (Cowork).

Stack: Python 3.11+, Flask 3, SQLite, vanilla HTML/CSS/JS. macOS runtime (launchd). No build step.

## File map

```
.
├── server/
│   ├── app.py            # Flask + /api/* routes
│   ├── db.py             # SQLite schema + helpers (oportunidades, execucoes, projetos)
│   ├── importer.py       # Parses `const BOOKMARKS = [...]` from HTML -> upsert into SQLite
│   ├── executor.py       # Claude×Cowork heuristic + pbcopy + osascript + git + gh
│   └── requirements.txt  # Flask 3.0+
├── index.html            # Single-page UI, vanilla JS
├── scripts/launchd/
│   ├── panel.plist.template     # Rendered by install-launchd.sh (replaces __LABEL__/__REPO__/__PORT__)
│   └── watchdog.plist.template
├── examples/
│   └── sample-relatorio.html    # Expected HTML source format (synthetic data)
├── setup.sh              # Idempotent setup
├── install-launchd.sh    # Registers launchd agents
├── start.sh              # Foreground run (debug)
├── stop.sh               # Stops everything
├── healthcheck.sh        # Watchdog, invoked by the plist every 5 min
└── .env.example          # Documented env vars
```

## Code conventions

- **Language**: code comments and UI strings stay in **pt-BR** (this is a pt-BR-first app). Function, variable, and class names in **English** when possible; the existing pt-BR identifiers (`oportunidade`, `executar`, `acao_sugerida`, `tipo_execucao`) stay for backward compatibility with the SQLite schema and API payload. **Documentation files (this one, README, DESIGN, CONTRIBUTING, CHANGELOG) are always in English.** A Portuguese README lives at `README.pt-BR.md`.
- **Python**: PEP 8, f-strings, `pathlib` over `os.path`, `from __future__ import annotations`, type hints when they help.
- **No ORM**: SQLite direct via `sqlite3` + `Row`. Schema lives in a single `SCHEMA` string plus an idempotent `migrate()` for new columns.
- **No frontend framework**: plain HTML + fetch. State at module level in a `state` object. No bundler.
- **Always idempotent**: `setup.sh`, `install-launchd.sh`, and `import_html()` must be safe to run 1 or 100 times.
- **No external deps on the hot path**: only Flask. `claude`, `gh`, and the Claude desktop app are optional — if missing, the panel logs and moves on.
- **Commits** in English, conventional-ish (`feat:`, `fix:`, `chore:`, `docs:`). Keep scope small.
- **Comment only when the "why" is non-obvious.** Don't document the "what" — the code says it.

## Main flows

### 1. Import bookmarks

```
relatorio-bookmarks-x.html  ->  importer.extract_bookmarks_array (regex)
                            ->  json.loads
                            ->  db.upsert_oportunidade (unique key: `link`)
```

Fields preserved on update: `status`, `tipo_execucao`, `notas`, `instalado`, `aplicado`, `projeto_iniciado`. The rest is overwritten by the HTML.

### 2. Execute an opportunity

```
POST /api/oportunidades/<id>/executar { tipo, criar_projeto, com_github }
  -> executor.executar(op_id, ...)
    -> heuristic_tipo(op)   (if tipo not forced)
    -> criar_projeto(op)    (optional: git init + CLAUDE.md + gh repo create)
    -> montar_prompt(op, tipo, projeto_path)
    -> pbcopy + osascript (Terminal) or open -a (Cowork)
    -> db.log_execucao + db.update_oportunidade(status='em_progresso')
```

### 3. Always-on

```
Main launchd plist    -> python server/app.py  (KeepAlive + Crashed + NetworkState)
Watchdog launchd plist -> healthcheck.sh       (StartInterval=300s)
                          -> curl /api/healthz
                          -> on failure: launchctl kickstart -k or reinstall
```

## Common tasks

- **New editable field on an opportunity**: add it to the migration inside `db.migrate()`, to the `allowed` set in `api_update()` (`app.py`), and to `cardHTML()` + its handler (`index.html`).
- **New classification heuristic**: edit `CODE_KEYWORDS` / `DESKTOP_KEYWORDS` / `CODE_CATEGORIES` / `DESKTOP_CATEGORIES` in `executor.py`. Mirror the same logic inside `recommendedTipo()` in `index.html` so the visual recommendation matches the backend.
- **New action button**: add it to `.actions-bar` in `cardHTML()` with a `data-act="..."` attribute, and a new branch in the `click` handler in `index.html`. If it needs a server-side side effect, create an endpoint in `app.py` and call it from `executor.py`.
- **New input HTML format**: swap the regex in `importer.extract_bookmarks_array()` or replace it with JSON/CSV parsing. The contract is the shape of the `row` dict passed to `upsert_oportunidade()` — keep those field names.

## Security

- Binds to `127.0.0.1` by default. **Don't flip it to `0.0.0.0` lightly** — the panel has no auth.
- Never commit `data/`, `.env`, `relatorio-bookmarks-x.html`, captures, triages, or profile analyses. `.gitignore` already blocks them, but double-check before any push.
- `gh` tokens live in the macOS keychain — the panel never reads them.
- Folders created by the **+ New project** button land under `<repo>/<slug>/` and are also ignored by the panel's `.gitignore`. Each spawned project keeps its own git.

## When Claude Code is invoked here

The panel is the tool. When you (Claude) are invoked **inside** a subfolder created by **+ New project**, that subfolder has its own `CLAUDE.md` with bookmark-specific instructions (objective, insight, suggested action). Follow that context, not this one.

This `CLAUDE.md` is for sessions that **edit the panel itself** (backend, UI, scripts, docs).

## Roadmap summary

See [README.md](README.md#roadmap) for the full list. Priorities: filterable execution history, webhook-based updates, CSV/JSON export.
