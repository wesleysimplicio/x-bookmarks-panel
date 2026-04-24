# X Bookmarks Panel

> 🇺🇸 English. Leia em português: [README.pt-BR.md](README.pt-BR.md).

A local panel that turns your saved **x.com** bookmarks into an actionable queue. It reads your curated bookmarks from an HTML file, stores them in SQLite, and drops an **Execute** button on every card — firing up either Claude Code (in a fresh project folder, with git and optional GitHub repo) or the Claude desktop app (Cowork), depending on the task type.

> Local-first. Nothing leaves your machine. No tokens, no external API, no telemetry.

---

## Why this exists

X bookmarks become a graveyard. You save a tweet at midnight swearing you'll come back to it, and it disappears in the scroll. This panel takes your triage output — whether manual, from an agent, from a scheduled task, or any pipeline that produces the expected HTML — and forces you to decide: **act now**, **study later**, or **archive**. One click dispatches the execution.

It assumes you already have Claude Code installed and, optionally, `gh` authenticated for automatic private repo creation.

---

## What it does

- Imports bookmarks from an HTML file (`relatorio-bookmarks-x.html`) containing a `const BOOKMARKS = [...]` array.
- Renders each item as a card with **insight**, **suggested action**, **priority**, and **category**.
- Classifies each item automatically between **Claude Code** (code task) and **Cowork** (desktop/visual task) via a simple heuristic — you can always override.
- On **Execute**:
  - **Claude Code**: copies the prompt to the clipboard and opens Terminal at the project path running `claude "<prompt>"`.
  - **Cowork**: copies the prompt and opens the Claude desktop app — paste with ⌘V.
  - **+ New project**: creates `<repo>/<slug>/`, writes `README.md` + `CLAUDE.md`, runs `git init` + initial commit. Optional: `gh repo create --private`.
- Tracks progress: **installed**, **applied**, **project started** (three independent flags per card).
- Debounced text search (`/` focuses, `Esc` clears).
- Always-on via launchd: panel restarts in ≤30s if it crashes, watchdog runs every 5min.

---

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ · Flask 3 · SQLite |
| Frontend | HTML + CSS + vanilla JS (no build step) |
| Runtime | macOS (launchd + Terminal.app + pbcopy + `open -a`) |
| External deps (optional) | [`claude`](https://docs.claude.com/en/docs/claude-code) CLI, [`gh`](https://cli.github.com/) CLI, Claude desktop app |

The panel itself only needs Python and Flask. Claude/gh/Cowork come in when you click **Execute** — if they're missing, the panel still works and just skips those actions.

---

## Setup

```bash
git clone https://github.com/wesleysimplicio/x-bookmarks-panel.git
cd x-bookmarks-panel
chmod +x setup.sh
./setup.sh
open http://localhost:8765
```

`setup.sh` is idempotent and does:

1. Copies `.env.example` → `.env` (if missing).
2. Creates `.venv/` and installs Flask.
3. Initializes SQLite at `data/bookmarks.db`.
4. Imports from HTML if present (`relatorio-bookmarks-x.html`).
5. Registers two launchd agents: the panel itself and a watchdog.

### First run without your own HTML

If you don't have a triage source yet, copy the sample:

```bash
cp examples/sample-relatorio.html relatorio-bookmarks-x.html
curl -X POST http://localhost:8765/api/oportunidades/import
```

That populates the panel with two synthetic bookmarks.

---

## Your bookmarks HTML

The panel expects a file named `relatorio-bookmarks-x.html` with a JavaScript block like this:

```html
<script>
const BOOKMARKS = [
  {
    "link": "https://x.com/username/status/123456789",
    "autor": "Display Name",
    "handle": "@username",
    "texto": "tweet body",
    "data": "2026-04-20",
    "midia": "texto|imagem|video|link",
    "categoria": "Claude Code",
    "prioridade": "agir-agora",
    "insight": "why this bookmark matters",
    "acao_sugerida": "what to do in practice",
    "vale_executar": true
  }
];
</script>
```

How you produce that HTML is up to you: manual curation, your own scraper, a scheduled task, a curation agent, whatever. See [`examples/sample-relatorio.html`](examples/sample-relatorio.html) for the full format. The importer is idempotent — already-imported links are updated, new ones are inserted, and your panel-edited fields (`status`, `tipo_execucao`, `notas`) are preserved.

> **Note on field names.** Internally the schema uses Portuguese names (`oportunidades`, `acao_sugerida`, `tipo_execucao`). They stay for backward compatibility with the existing SQLite schema and API payload. Feel free to open an issue if you want an English-aliased API on top.

---

## Architecture in 30 seconds

```
Triage HTML  →  importer.py  →  SQLite (oportunidades)
                                     ↓
                                Flask app.py  ←→  index.html (fetch)
                                     ↓
                                executor.py  →  pbcopy + osascript + gh
                                              (Claude Code / Cowork / git / GitHub)
```

| File | Purpose |
|------|---------|
| [server/app.py](server/app.py) | Flask + REST routes |
| [server/db.py](server/db.py) | SQLite schema + helpers |
| [server/importer.py](server/importer.py) | Reads the `BOOKMARKS` array from HTML |
| [server/executor.py](server/executor.py) | Opens Terminal/Cowork, scaffolds folder + git + `gh repo create` |
| [index.html](index.html) | Vanilla-JS UI |

More architectural detail in [DESIGN.md](DESIGN.md).

---

## API

The UI consumes these endpoints. You can automate outside the panel the same way:

| Method | Path | Body |
|--------|------|------|
| GET  | `/api/healthz` | — |
| GET  | `/api/stats` | — |
| GET  | `/api/oportunidades?prioridade=&status=&categoria=` | — |
| GET  | `/api/oportunidades/<id>` | — |
| POST | `/api/oportunidades/<id>` | `{status?, tipo_execucao?, notas?, prioridade?, instalado?, aplicado?, projeto_iniciado?}` |
| POST | `/api/oportunidades/<id>/executar` | `{tipo?: 'claude'\|'cowork'\|'auto', criar_projeto?: bool, com_github?: bool}` |
| POST | `/api/oportunidades/import` | — |
| GET  | `/api/projetos` | — |

Example:

```bash
# Re-import on demand
curl -X POST http://localhost:8765/api/oportunidades/import

# Fire Claude Code + new folder + private GitHub repo
curl -X POST http://localhost:8765/api/oportunidades/1/executar \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"claude","criar_projeto":true,"com_github":true}'
```

---

## Environment variables

Edit `.env` (auto-created by `setup.sh`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOOKMARKS_PORT` | `8765` | Panel HTTP port |
| `BOOKMARKS_HOST` | `127.0.0.1` | Bind address (keep local; do not expose) |
| `BOOKMARKS_LABEL_PREFIX` | `com.bookmarks.panel` | launchd label prefix |
| `COWORK_APP` | `Claude` | Desktop app name that `open -a` targets |
| `BOOKMARKS_HTML` | `<repo>/relatorio-bookmarks-x.html` | Alternate HTML source path |

---

## Commands

```bash
./setup.sh                 # full setup (idempotent)
./install-launchd.sh       # (re)register as always-on service
./start.sh                 # run in foreground for debug (Ctrl+C to exit)
./stop.sh                  # unload launchd + kill process
./healthcheck.sh           # manual ping + restart if down

launchctl list | grep bookmarks    # agent status
tail -f data/painel.log             # server logs
tail -f data/healthcheck.log        # watchdog logs
```

---

## Always-on guarantees

| Scenario | What happens |
|----------|--------------|
| Server crashes (exception, `kill -9`) | launchd restarts in ≤30s (`KeepAlive` + `ThrottleInterval`) |
| Server goes zombie (alive but unresponsive) | watchdog detects in ≤5min and runs `kickstart -k` |
| Plist missing / launchd unloaded | watchdog runs `install-launchd.sh` |
| Mac reboots | comes back on login (`RunAtLoad`) |
| Mac sleeps/wakes | comes back on network availability (`NetworkState=true`) |

---

## Troubleshooting

- **"Server offline"** — `tail -n 50 data/painel.err.log`. If empty, `launchctl list | grep bookmarks`.
- **Watchdog not recovering** — `tail data/healthcheck.log`.
- **Cowork button doesn't open the app** — confirm the app is called `Claude` in Finder. If not, adjust `COWORK_APP` in `.env`.
- **Terminal can't find `claude`** — `which claude`. If not under `/opt/homebrew/bin` or `/usr/local/bin`, update the `PATH` inside `scripts/launchd/panel.plist.template` and run `./install-launchd.sh`.
- **`gh repo create` fails** — run `gh auth login` once.
- **DB corrupted** — `./stop.sh && rm data/bookmarks.db && ./setup.sh`.

---

## Privacy and security

- The panel binds to `127.0.0.1` — nobody on your network reaches it.
- Zero telemetry. Zero remote auth. Zero tokens in the repo.
- `.gitignore` blocks `data/`, `*.db`, `relatorio-bookmarks-x.html`, `.env`, captures, triages, profile analyses, and the folders generated by the **+ New project** button.
- Before publishing your own fork: confirm `git status` doesn't list anything sensitive.

---

## Roadmap

- [ ] Filterable execution history in the UI.
- [ ] Webhook that re-imports when the external triage pipeline runs (instead of polling).
- [ ] `POST /api/projetos/<id>/abrir` endpoint to reopen Claude Code in an existing project.
- [ ] CSV/JSON export for bookmarks.
- [ ] Linux support (currently depends on `launchctl` + `pbcopy` + AppleScript).

---

## Contributing

PRs welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
