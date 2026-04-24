# DESIGN.md — Decisões de arquitetura

Por que o projeto é desse jeito. Quem está lendo pra entender, estender ou contestar, comece aqui.

## Princípios

1. **Local-first, sempre.** O painel roda no Mac do usuário, escuta em `127.0.0.1`, guarda tudo em SQLite local. Nenhuma rede externa no hot path. Nenhum token no repo.
2. **Menor peça que funciona.** Flask + SQLite + HTML vanilla. Sem ORM, sem bundler, sem frontend framework, sem container. Quem lê a codebase em 10min consegue fazer PR.
3. **Idempotência em tudo que toca o SO.** `setup.sh`, `install-launchd.sh`, `import_html()` podem rodar 1 ou 100 vezes — o resultado é o mesmo.
4. **Curadoria é plugável.** O painel não faz triagem; ele lê o resultado da triagem. O contrato é um arquivo HTML com o array `BOOKMARKS`. De onde vem (você, um agente, um scraper, um cron) é irrelevante pro painel.
5. **Falhas externas não param o núcleo.** Faltou `gh`? Loga e segue. Faltou o app Claude? Cola no clipboard mesmo assim. Faltou o HTML? Painel sobe vazio e te mostra zero cards.

---

## Decisões com trade-offs

### Flask (não FastAPI / Starlette / Express)

Escolha: Flask 3 puro, sem Blueprints.

**Por quê**: o app inteiro cabe num único `app.py` de ~140 linhas. Não precisa async — as operações lentas (osascript, subprocess, launchctl) são chamadas do Mac e já bloqueiam o request do usuário mesmo. Latência não importa aqui; a UI faz polling de 60s.

**Custo**: se um dia precisar abrir WebSockets pra push-updates, muda pra FastAPI + uvicorn. Migração trivial porque as rotas são idiomáticas.

### SQLite (não Postgres / DuckDB / arquivo JSON)

Escolha: SQLite com schema SQL puro em `server/db.py:SCHEMA`.

**Por quê**: um arquivo, zero servidor, transações ACID, suporta triggers (usado pra `updated_at`), e FK on-delete. Cabem dezenas de milhares de bookmarks numa query em <10ms.

**Custo**: concorrência é single-writer. Como o painel só aceita writes do próprio usuário via UI, isso não importa.

### Sem ORM

Escolha: `sqlite3` + `Row` direto.

**Por quê**: schema cabe na cabeça. SQLAlchemy/Peewee adicionariam uma camada que não puxa o próprio peso num projeto dessa escala. `PRAGMA foreign_keys = ON` + um `migrate()` idempotente resolve evolução.

### Heurística de classificação vs ML

Escolha: listas de keywords (`CODE_KEYWORDS`, `DESKTOP_KEYWORDS`) + bônus por categoria.

**Por quê**: a taxonomia é do próprio usuário. Quando ele vê uma classificação errada, edita a keyword ou clica no outro botão — leva 2s. Um classificador ML seria over-engineering, treinaria em dados escassos, e ainda precisaria do override manual.

A UI espelha a heurística em `index.html:recommendedTipo()` pra sinalização visual. Manter as duas listas em sincronia é manual (regra escrita em [CLAUDE.md](CLAUDE.md) pra quem editar).

### launchd (não systemd / cron / PM2)

Escolha: dois user agents launchd + watchdog periódico.

**Por quê**: o target é macOS, e `launchd` é o nativo. `KeepAlive` + `Crashed=true` + `NetworkState=true` cobrem os casos de crash, wake-from-sleep e boot. Um segundo agent (`StartInterval=300`) roda o `healthcheck.sh` pra pegar o cenário "processo vivo mas não responde" — algo que `KeepAlive` sozinho não resolve.

**Custo**: não portável pra Linux. Quando alguém quiser rodar lá, substitui os dois plists por um systemd service com `Restart=always` + um timer pra healthcheck. Os scripts em bash são independentes.

### Botão "+ Novo projeto" cria repositório com `gh`

Escolha: o painel delega a criação pra `gh repo create --private --source . --push`.

**Por quê**: usar a CLI oficial do GitHub evita manter token OAuth no painel. O `gh` já cuida de auth, keyring, 2FA e erros de rede. Quando `gh` não está instalado ou autenticado, o painel cria o repo local com `git init` e pula a parte remota.

### Clipboard + osascript pra acionar o Claude Code

Escolha: `pbcopy(prompt)` + `open terminal with command "claude '<prompt>'"` via AppleScript.

**Por quê**: o Claude Code é uma CLI de terminal. Pra passar um prompt longo de forma confiável, duas opções: `claude "$(pbpaste)"` (frágil com aspas/quebras de linha) ou passar inline via `shlex.quote`. Optamos pela segunda, com o clipboard como plano B — se o terminal falhar, o usuário ainda tem o prompt pra colar manualmente.

O mesmo raciocínio vale pra Cowork: `open -a "Claude"` não aceita argumento de texto, então a única via é o clipboard + ⌘V manual.

---

## Modelo de dados

Três tabelas em `server/db.py:SCHEMA`.

### `oportunidades` (uma linha por bookmark)

| Coluna | Tipo | Notas |
|--------|------|-------|
| `id` | INT PK | autoincrement |
| `link` | TEXT UNIQUE | chave lógica — URL do post no x.com |
| `autor`, `handle`, `texto`, `data_bookmark`, `midia` | TEXT | metadados do tweet |
| `categoria`, `prioridade`, `insight`, `acao_sugerida` | TEXT | output da triagem |
| `vale_executar` | INT (0/1) | flag vinda do HTML |
| `status` | TEXT CHECK | `novo` \| `em_progresso` \| `executado` \| `arquivado` \| `descartado` |
| `tipo_execucao` | TEXT | `claude` \| `cowork` \| NULL (decide pela heurística) |
| `notas` | TEXT | anotação livre do usuário |
| `instalado`, `aplicado`, `projeto_iniciado` | INT (0/1) | flags de progresso independentes |
| `created_at`, `updated_at` | TEXT | `updated_at` via trigger |

### `execucoes` (log append-only)

Cada clique em **Executar** cria uma linha. Guarda `tipo`, `prompt` gerado, `projeto_path` (se criou pasta), `status` (`iniciada` → `concluida` \| `erro`) e um `log` textual com timestamps.

### `projetos` (pastas scaffoldadas)

Quando o usuário clica **+ Novo projeto**, o painel cria `<repo>/<slug>/` e registra aqui. `slug` é UNIQUE; colisões recebem sufixo numérico.

---

## API REST

Todas as rotas retornam JSON. Estado dos cards é derivado da tabela `oportunidades`.

Contrato resumido (formato completo no [README](README.md#api)):

- `GET /api/stats` — contadores agregados pra header
- `GET /api/oportunidades` — lista com filtros opcionais (`status`, `prioridade`, `categoria`)
- `POST /api/oportunidades/<id>` — update parcial com allowlist de campos
- `POST /api/oportunidades/<id>/executar` — dispatch: retorna `{ok, exec_id, tipo, projeto?, log}`
- `POST /api/oportunidades/import` — re-lê o HTML

O frontend usa polling de 60s (`setInterval(refresh, 60_000)`). Sem WebSocket, sem SSE — a frequência de edição é baixa e o cenário é single-user.

---

## Decisões explicitamente evitadas

- **Autenticação**: não tem. O painel só escuta em `127.0.0.1`. Quem tem acesso ao Mac tem acesso aos cards.
- **Multi-usuário**: não suportado. Uma instância, um usuário, um SQLite.
- **Deploy remoto**: fora de escopo. O projeto é local-first por design.
- **Upload/arrastar HTML**: o importador lê do disco. Se quiser automatizar, um cron ou o próprio pipeline de triagem escreve o HTML e chama `POST /api/oportunidades/import`.
- **Tags livres / folksonomia**: `categoria` é uma coluna simples de string. Evitamos tabela `tags` + N:N porque o uso real não pediu.

---

## Evolução futura (hipótese)

- **Histórico filtrável** (já existe no DB, falta tela) — baixo esforço.
- **Webhook de atualização** — quando o pipeline externo gerar HTML novo, chamar `POST /api/oportunidades/import` em vez de polling. Elimina latência de até 60s.
- **Linux support** — substituir launchd por systemd, AppleScript por `xdotool`/`xclip`. Isolar o código macOS-específico num módulo `server/_macos.py`.
- **Export** — endpoint `GET /api/oportunidades.csv` com streaming.

Cada item só entra quando alguém tem o problema — não especulativamente.
