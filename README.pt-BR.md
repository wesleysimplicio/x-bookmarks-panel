# X Bookmarks Panel — Português

> 🇧🇷 Versão em português. Read this in English: [README.md](README.md).

Painel local que transforma bookmarks salvos do **x.com** numa esteira acionável. Lê um HTML com sua curadoria, guarda tudo em SQLite, e coloca um botão **Executar** em cada item — abrindo o Claude Code (em pasta nova, com git + GitHub opcional) ou o app Claude desktop (Cowork) conforme o tipo de tarefa.

> Local-first. Nenhum dado sai da sua máquina. Sem tokens, sem API externa, sem telemetria.

---

## Por que isso existe

Bookmark do X vira um cemitério. Você salva um tweet de madrugada prometendo voltar, e ele some no scroll. Este painel pega a sua triagem — seja manual, vinda de um agente, de uma scheduled task, ou de qualquer pipeline que produza o HTML no formato esperado — e te força a decidir: **agir agora**, **estudar depois** ou **arquivar**. Um clique dispara a execução.

Ele assume que você já tem o Claude Code instalado e, opcionalmente, o `gh` autenticado para criar repos privados automaticamente.

---

## O que faz

- Importa bookmarks de um HTML (`relatorio-bookmarks-x.html`) com um array `const BOOKMARKS = [...]`.
- Mostra cada item como card com **insight**, **ação sugerida**, **prioridade** e **categoria**.
- Classifica automaticamente entre **Claude Code** (tarefa de código) e **Cowork** (tarefa visual/desktop) por heurística simples — você pode sobrescrever.
- Ao clicar **Executar**:
  - **Claude Code**: copia o prompt pro clipboard e abre o Terminal no diretório do projeto rodando `claude "<prompt>"`.
  - **Cowork**: copia o prompt e abre o app Claude — você cola com ⌘V.
  - **+ Novo projeto**: cria `<repo>/<slug>/`, escreve `README.md` + `CLAUDE.md`, faz `git init` + primeiro commit. Opcional: `gh repo create --private`.
- Marca progresso: **instalado**, **aplicado**, **projeto iniciado** (flags independentes por card).
- Busca textual com debounce (`/` foca, `Esc` limpa).
- Serviço launchd sempre-online: painel reinicia em ≤30s se cair, watchdog a cada 5min.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11+ · Flask 3 · SQLite |
| Frontend | HTML + CSS + JS vanilla (zero build) |
| Runtime | macOS (launchd + Terminal.app + pbcopy + `open -a`) |
| Deps externas (opcionais) | [`claude`](https://docs.claude.com/en/docs/claude-code) CLI, [`gh`](https://cli.github.com/) CLI, app Claude desktop |

O painel só precisa de Python e Flask. Claude/gh/Cowork entram quando você clica **Executar** — se não estiverem instalados, o painel segue funcionando e só pula essas ações.

---

## Setup

```bash
git clone https://github.com/<seu-usuario>/x-bookmarks-panel.git
cd x-bookmarks-panel
chmod +x setup.sh
./setup.sh
open http://localhost:8765
```

O `setup.sh` é idempotente e faz:

1. Copia `.env.example` → `.env` (se não existir).
2. Cria `.venv/` e instala Flask.
3. Inicia o SQLite em `data/bookmarks.db`.
4. Importa do HTML se existir (`relatorio-bookmarks-x.html`).
5. Registra dois launchd agents: o painel e um watchdog.

### Primeiro teste sem seu HTML

Se ainda não tem uma fonte de triagem, copie o exemplo:

```bash
cp examples/sample-relatorio.html relatorio-bookmarks-x.html
curl -X POST http://localhost:8765/api/oportunidades/import
```

Isso popula o painel com dois bookmarks sintéticos.

---

## Seu HTML de bookmarks

O painel espera um arquivo `relatorio-bookmarks-x.html` com um bloco JavaScript assim:

```html
<script>
const BOOKMARKS = [
  {
    "link": "https://x.com/usuario/status/123456789",
    "autor": "Nome Exibido",
    "handle": "@usuario",
    "texto": "conteúdo do tweet",
    "data": "2026-04-20",
    "midia": "texto|imagem|video|link",
    "categoria": "Claude Code",
    "prioridade": "agir-agora",
    "insight": "por que este bookmark importa",
    "acao_sugerida": "o que fazer na prática",
    "vale_executar": true
  }
];
</script>
```

Como você produz esse HTML é problema seu: manual, scraper próprio, uma scheduled task, um agente de curadoria. Veja [`examples/sample-relatorio.html`](examples/sample-relatorio.html) para o formato completo. O importer é idempotente — já importados são atualizados, novos são inseridos, e seus campos editados no painel (`status`, `tipo_execucao`, `notas`) são preservados.

---

## Arquitetura em 30 segundos

```
HTML de triagem  →  importer.py  →  SQLite (oportunidades)
                                         ↓
                                   Flask app.py  ←→  index.html (fetch)
                                         ↓
                                   executor.py  →  pbcopy + osascript + gh
                                                  (Claude Code / Cowork / git / GitHub)
```

| Arquivo | Função |
|---------|--------|
| [server/app.py](server/app.py) | Flask + rotas REST |
| [server/db.py](server/db.py) | Schema SQLite + helpers |
| [server/importer.py](server/importer.py) | Lê array `BOOKMARKS` do HTML |
| [server/executor.py](server/executor.py) | Abre Terminal/Cowork, cria pasta + git + `gh repo create` |
| [index.html](index.html) | UI em JS vanilla |

Mais detalhes arquiteturais em [DESIGN.md](DESIGN.md).

---

## API

Toda a UI consome esses endpoints. Você pode automatizar de fora igual:

| Método | Path | Body |
|--------|------|------|
| GET  | `/api/healthz` | — |
| GET  | `/api/stats` | — |
| GET  | `/api/oportunidades?prioridade=&status=&categoria=` | — |
| GET  | `/api/oportunidades/<id>` | — |
| POST | `/api/oportunidades/<id>` | `{status?, tipo_execucao?, notas?, prioridade?, instalado?, aplicado?, projeto_iniciado?}` |
| POST | `/api/oportunidades/<id>/executar` | `{tipo?: 'claude'\|'cowork'\|'auto', criar_projeto?: bool, com_github?: bool}` |
| POST | `/api/oportunidades/import` | — |
| GET  | `/api/projetos` | — |

Exemplo:

```bash
# Re-importar sob demanda
curl -X POST http://localhost:8765/api/oportunidades/import

# Disparar Claude Code + pasta nova + repo privado no GitHub
curl -X POST http://localhost:8765/api/oportunidades/1/executar \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"claude","criar_projeto":true,"com_github":true}'
```

---

## Variáveis de ambiente

Edite o `.env` (criado automaticamente pelo `setup.sh`):

| Variável | Padrão | O que faz |
|----------|--------|-----------|
| `BOOKMARKS_PORT` | `8765` | Porta do painel |
| `BOOKMARKS_HOST` | `127.0.0.1` | Bind (deixe local; não exponha) |
| `BOOKMARKS_LABEL_PREFIX` | `com.bookmarks.panel` | Prefixo dos labels launchd |
| `COWORK_APP` | `Claude` | Nome do app desktop que o `open -a` abre |
| `BOOKMARKS_HTML` | `<repo>/relatorio-bookmarks-x.html` | Caminho alternativo do HTML |

---

## Comandos

```bash
./setup.sh                 # setup completo (idempotente)
./install-launchd.sh       # (re)registra como serviço sempre-online
./start.sh                 # roda em foreground pra debug (Ctrl+C sai)
./stop.sh                  # descarrega launchd + mata processo
./healthcheck.sh           # ping manual no painel + restart se cair

launchctl list | grep bookmarks    # status dos agents
tail -f data/painel.log             # logs do server
tail -f data/healthcheck.log        # logs do watchdog
```

---

## Garantias de sempre-online

| Cenário | O que acontece |
|---------|----------------|
| Server crasha (exception, `kill -9`) | launchd reinicia em ≤30s (`KeepAlive` + `ThrottleInterval`) |
| Server fica zumbi (vivo mas não responde) | watchdog detecta em ≤5min e dá `kickstart -k` |
| Plist some / launchd descarregado | watchdog roda `install-launchd.sh` |
| Mac reinicia | sobe no login (`RunAtLoad`) |
| Mac dorme/acorda | sobe quando rede volta (`NetworkState=true`) |

---

## Troubleshooting

- **"Server offline"** — `tail -n 50 data/painel.err.log`. Se vazio, `launchctl list | grep bookmarks`.
- **Watchdog não ressuscita** — `tail data/healthcheck.log`.
- **Botão Cowork não abre o app** — confirma que o app é `Claude` no Finder. Se for outro, ajusta `COWORK_APP` no `.env`.
- **`claude` não encontrado pelo Terminal** — `which claude`. Se não estiver em `/opt/homebrew/bin` ou `/usr/local/bin`, ajuste o `PATH` dentro de `scripts/launchd/panel.plist.template` e rode `./install-launchd.sh`.
- **`gh repo create` falha** — `gh auth login` uma vez.
- **DB corrompeu** — `./stop.sh && rm data/bookmarks.db && ./setup.sh`.

---

## Privacidade e segurança

- O painel escuta em `127.0.0.1` — ninguém na sua rede alcança.
- Zero telemetria. Zero auth remota. Zero token no repo.
- O `.gitignore` bloqueia `data/`, `*.db`, `relatorio-bookmarks-x.html`, `.env`, capturas, triagens, análises de perfil e as pastas geradas pelo botão **+ Novo projeto**.
- Antes de publicar o seu fork: confirme que `git status` não lista nada sensível.

---

## Roadmap

- [ ] Histórico de execuções filtrável na UI.
- [ ] Webhook pra atualizar quando o pipeline de triagem rodar (em vez de polling).
- [ ] Endpoint `POST /api/projetos/<id>/abrir` pra reabrir Claude Code num projeto existente.
- [ ] Export CSV/JSON dos bookmarks.
- [ ] Suporte a Linux (hoje depende de `launchctl` + `pbcopy` + AppleScript).

---

## Contribuindo

PRs bem-vindos. Leia [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[MIT](LICENSE).
