# DESIGN.md — Architecture decisions

Why the project is the way it is. If you're reading to understand, extend, or push back on it, start here.

## Principles

1. **Local-first, always.** The panel runs on the user's Mac, listens on `127.0.0.1`, and stores everything in local SQLite. No external network on the hot path. No tokens in the repo.
2. **Smallest thing that works.** Flask + SQLite + vanilla HTML. No ORM, no bundler, no frontend framework, no container. Someone who reads the codebase for 10 minutes can ship a PR.
3. **Idempotent for anything that touches the OS.** `setup.sh`, `install-launchd.sh`, `import_html()` can run once or a hundred times — same result.
4. **Curation is pluggable.** The panel doesn't triage; it reads the output of your triage. The contract is an HTML file with a `BOOKMARKS` array. Where it comes from (you, an agent, a scraper, a cron) is irrelevant to the panel.
5. **External failures don't break the core.** `gh` missing? Log and continue. Claude app missing? Still copy to clipboard. HTML missing? Panel boots empty and shows zero cards.

---

## Decisions with trade-offs

### Flask (not FastAPI / Starlette / Express)

Pick: plain Flask 3, no Blueprints.

**Why**: the whole app fits in a single ~140-line `app.py`. No need for async — the slow operations (osascript, subprocess, launchctl) are Mac calls that would block the user's request anyway. Latency doesn't matter here; the UI polls every 60s.

**Cost**: if push-updates via WebSockets ever become relevant, switch to FastAPI + uvicorn. Migration is trivial because the routes are idiomatic.

### SQLite (not Postgres / DuckDB / JSON file)

Pick: SQLite with plain SQL schema in `server/db.py:SCHEMA`.

**Why**: a single file, no server, ACID transactions, triggers (used for `updated_at`), and FK on-delete. Tens of thousands of bookmarks finish a query in <10ms.

**Cost**: concurrency is single-writer. Since the panel only accepts writes from the UI owner, this is fine.

### No ORM

Pick: `sqlite3` + `Row` directly.

**Why**: the schema fits in your head. SQLAlchemy/Peewee would add a layer that doesn't pay for itself at this scale. `PRAGMA foreign_keys = ON` plus an idempotent `migrate()` covers evolution.

### Heuristic classification vs ML

Pick: keyword lists (`CODE_KEYWORDS`, `DESKTOP_KEYWORDS`) plus category bonuses.

**Why**: the taxonomy belongs to the user. When a classification misses, they edit a keyword or click the other button — 2 seconds. An ML classifier would be over-engineering, would train on scarce data, and would still need manual override.

The UI mirrors the heuristic in `index.html:recommendedTipo()` for visual hinting. Keeping the two lists in sync is manual (documented in [CLAUDE.md](CLAUDE.md) for anyone editing them).

### launchd (not systemd / cron / PM2)

Pick: two launchd user agents plus a periodic watchdog.

**Why**: macOS is the target, and `launchd` is native. `KeepAlive` + `Crashed=true` + `NetworkState=true` cover crashes, wake-from-sleep, and boot. A second agent (`StartInterval=300`) runs `healthcheck.sh` to catch the "process alive but unresponsive" case — something `KeepAlive` alone can't.

**Cost**: not portable to Linux. When someone wants to run it there, swap the two plists for a systemd service with `Restart=always` plus a timer for the healthcheck. The bash scripts are independent.

### "+ New project" uses `gh` to create the repository

Pick: the panel delegates remote creation to `gh repo create --private --source . --push`.

**Why**: using the official GitHub CLI avoids storing an OAuth token in the panel. `gh` already handles auth, keychain, 2FA, and network errors. When `gh` isn't installed or authenticated, the panel still creates the local repo with `git init` and skips the remote step.

### Clipboard + osascript to invoke Claude Code

Pick: `pbcopy(prompt)` + `open terminal with command "claude '<prompt>'"` via AppleScript.

**Why**: Claude Code is a terminal CLI. To hand it a long prompt reliably there are two options: `claude "$(pbpaste)"` (fragile with quotes/newlines) or pass inline via `shlex.quote`. We went with the second, with the clipboard as a safety net — if the terminal invocation fails, the user still has the prompt ready to paste manually.

Same reasoning for Cowork: `open -a "Claude"` takes no text argument, so clipboard + manual ⌘V is the only path.

---

## Data model

Three tables in `server/db.py:SCHEMA`.

### `oportunidades` (one row per bookmark)

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | autoincrement |
| `link` | TEXT UNIQUE | logical key — post URL on x.com |
| `autor`, `handle`, `texto`, `data_bookmark`, `midia` | TEXT | tweet metadata |
| `categoria`, `prioridade`, `insight`, `acao_sugerida` | TEXT | triage output |
| `vale_executar` | INT (0/1) | flag coming from the HTML |
| `status` | TEXT CHECK | `novo` \| `em_progresso` \| `executado` \| `arquivado` \| `descartado` |
| `tipo_execucao` | TEXT | `claude` \| `cowork` \| NULL (falls back to heuristic) |
| `notas` | TEXT | user free-form notes |
| `instalado`, `aplicado`, `projeto_iniciado` | INT (0/1) | independent progress flags |
| `created_at`, `updated_at` | TEXT | `updated_at` via trigger |

### `execucoes` (append-only log)

Every **Execute** click creates a row. Stores `tipo`, generated `prompt`, `projeto_path` (if a folder was created), `status` (`iniciada` → `concluida` \| `erro`), and a textual `log` with timestamps.

### `projetos` (scaffolded folders)

When the user clicks **+ New project**, the panel creates `<repo>/<slug>/` and records it here. `slug` is UNIQUE; collisions get a numeric suffix.

> Field names stay in pt-BR to preserve the existing schema and API payload. If you want an English-aliased public API, open an issue.

---

## REST API

All routes return JSON. Card state is derived from the `oportunidades` table.

Contract summary (full format in the [README](README.md#api)):

- `GET /api/stats` — aggregate counters for the header.
- `GET /api/oportunidades` — list with optional filters (`status`, `prioridade`, `categoria`).
- `POST /api/oportunidades/<id>` — partial update with an allowlist of fields.
- `POST /api/oportunidades/<id>/executar` — dispatch: returns `{ok, exec_id, tipo, projeto?, log}`.
- `POST /api/oportunidades/import` — re-reads the HTML.

The frontend uses 60s polling (`setInterval(refresh, 60_000)`). No WebSocket, no SSE — edit frequency is low and the scenario is single-user.

---

## Explicitly avoided

- **Authentication**: none. The panel only listens on `127.0.0.1`. Whoever has access to the Mac has access to the cards.
- **Multi-user**: unsupported. One instance, one user, one SQLite file.
- **Remote deploy**: out of scope. Local-first by design.
- **HTML upload / drag-drop**: the importer reads from disk. To automate, a cron or the triage pipeline itself writes the HTML and calls `POST /api/oportunidades/import`.
- **Free-form tags / folksonomy**: `categoria` is a plain text column. We skipped a N:N `tags` table because real usage didn't demand it.

---

## Possible evolution

- **Filterable history** (DB is ready, screen is missing) — low effort.
- **Update webhook** — when the external triage pipeline produces a new HTML, call `POST /api/oportunidades/import` instead of polling. Kills the up-to-60s staleness.
- **Linux support** — swap launchd for systemd, AppleScript for `xdotool`/`xclip`. Isolate macOS-specific code into `server/_macos.py`.
- **Export** — `GET /api/oportunidades.csv` with streaming.

Each item only lands when someone actually has the problem — never speculatively.
