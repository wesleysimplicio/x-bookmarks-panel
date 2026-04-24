# CLAUDE.md — Contexto do projeto

Arquivo lido automaticamente pelo Claude Code ao iniciar sessão na raiz deste repo. Mantém contexto persistente entre sessões.

## Sobre o projeto

Painel local pra triagem de bookmarks do **x.com**. Lê um HTML com curadoria (`relatorio-bookmarks-x.html`), persiste em SQLite (`data/bookmarks.db`) e expõe cards com botão **Executar** que disparam o Claude Code ou o app Claude desktop (Cowork).

Stack: Python 3.11+, Flask 3, SQLite, HTML/CSS/JS vanilla. Runtime macOS (launchd). Zero build step.

## Mapa de arquivos

```
.
├── server/
│   ├── app.py            # Flask + rotas /api/*
│   ├── db.py             # Schema SQLite + helpers (oportunidades, execucoes, projetos)
│   ├── importer.py       # Lê `const BOOKMARKS = [...]` do HTML → upsert no SQLite
│   ├── executor.py       # Heurística Claude×Cowork + pbcopy + osascript + git + gh
│   └── requirements.txt  # Flask 3.0+
├── index.html            # UI single-page, JS vanilla
├── scripts/launchd/
│   ├── panel.plist.template     # Substitui __LABEL__/__REPO__/__PORT__ em install-launchd.sh
│   └── watchdog.plist.template
├── examples/
│   └── sample-relatorio.html    # Formato esperado do HTML fonte (dados sintéticos)
├── setup.sh              # Setup idempotente
├── install-launchd.sh    # Registra os agents no launchd
├── start.sh              # Roda em foreground (debug)
├── stop.sh               # Para tudo
├── healthcheck.sh        # Watchdog, chamado pelo plist a cada 5min
└── .env.example          # Variáveis de ambiente documentadas
```

## Convenções de código

- **Idioma**: comentários + strings de UI em **pt-BR**. Nomes de funções, variáveis e classes em **inglês** quando possível; os existentes em pt-BR (`oportunidade`, `executar`, `acao_sugerida`, `tipo_execucao`) ficam pra preservar compatibilidade com o schema do SQLite e o payload da API.
- **Python**: PEP 8, f-strings, `pathlib` sobre `os.path`, `from __future__ import annotations`, type hints quando ajudam.
- **Sem ORM**: SQLite direto via `sqlite3` + `Row`. Schema em `SCHEMA` (string única) + `migrate()` idempotente pra colunas novas.
- **Sem framework frontend**: HTML + fetch. Estado em módulo-level `state`, sem bundler.
- **Idempotência sempre**: `setup.sh`, `install-launchd.sh`, `import_html()` podem rodar 1 ou 100 vezes.
- **Zero deps externas no hot path**: só Flask. `claude`, `gh` e o app Claude são opcionais — se faltarem, o painel loga e segue.
- **Commits** em inglês, conventional-ish (`feat:`, `fix:`, `chore:`, `docs:`). Escopo curto.
- **Comentário só quando o "porquê" é não-óbvio.** Não documentar o "o que" — código fala sozinho.

## Fluxos principais

### 1. Importar bookmarks

```
relatorio-bookmarks-x.html  →  importer.extract_bookmarks_array (regex)
                            →  json.loads
                            →  db.upsert_oportunidade (por `link` UNIQUE)
```

Campos preservados em update: `status`, `tipo_execucao`, `notas`, `instalado`, `aplicado`, `projeto_iniciado`. Demais são sobrescritos pelo HTML.

### 2. Executar uma oportunidade

```
POST /api/oportunidades/<id>/executar { tipo, criar_projeto, com_github }
  → executor.executar(op_id, ...)
    → heuristic_tipo(op) se tipo não foi forçado
    → criar_projeto(op)  (opcional: git init + CLAUDE.md + gh repo create)
    → montar_prompt(op, tipo, projeto_path)
    → pbcopy + osascript (Terminal) ou open -a (Cowork)
    → db.log_execucao + db.update_oportunidade(status='em_progresso')
```

### 3. Sempre-online

```
launchd plist principal  → python server/app.py  (KeepAlive + Crashed + NetworkState)
launchd plist watchdog   → healthcheck.sh  (StartInterval=300s)
                           → curl /api/healthz
                           → se falhar: launchctl kickstart -k ou reinstalar
```

## Coisas comuns pra mexer

- **Novo campo editável na oportunidade**: adicionar na migração dentro de `db.migrate()`, no set `allowed` do `api_update()` em `app.py`, e na UI em `cardHTML()` + handler.
- **Nova heurística de classificação**: editar `CODE_KEYWORDS` / `DESKTOP_KEYWORDS` / `CODE_CATEGORIES` / `DESKTOP_CATEGORIES` em `executor.py`. Refletir a mesma lógica em `recommendedTipo()` no `index.html` pra sinalização visual bater com o backend.
- **Novo botão de ação**: adicionar no `.actions-bar` do `cardHTML()` com `data-act="..."`, e um branch novo no handler de `click` em `index.html`. Se precisa de side effect no servidor, criar endpoint em `app.py` e chamar de `executor.py`.
- **Novo formato de HTML de entrada**: trocar a regex em `importer.extract_bookmarks_array()` ou substituir por parse de JSON/CSV direto. O contrato do `upsert_oportunidade()` é a forma do `row` — mantenha os nomes dos campos.

## Segurança

- Bind em `127.0.0.1` por padrão. **Não mude pra `0.0.0.0` sem pensar duas vezes** — o painel não tem auth.
- Nunca commite `data/`, `.env`, `relatorio-bookmarks-x.html`, capturas, triagens ou análises de perfil. O `.gitignore` já bloqueia, mas confira antes de qualquer push.
- Tokens do `gh` ficam no keyring do macOS — o painel nunca os lê.
- As pastas criadas pelo botão **+ Novo projeto** entram em `<repo>/<slug>/` e também são ignoradas pelo `.gitignore` do painel. Cada projeto tem o próprio git.

## Quando Claude Code é chamado aqui

O painel é a ferramenta. Quando você (Claude) é acionado **dentro** de uma subpasta criada por **+ Novo projeto**, o `CLAUDE.md` daquela subpasta tem instruções específicas do bookmark que deu origem (objetivo, insight, ação sugerida). Siga aquele contexto, não este.

Este `CLAUDE.md` aqui é pra sessões que **editam o painel em si** (backend, UI, scripts, docs).

## Roadmap resumido

Ver [README.md](README.md#roadmap) pra lista completa. Prioridade alta: histórico filtrável, webhook de atualização, export CSV/JSON.
