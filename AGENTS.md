# AGENTS.md

> Master instruction file lido por **Claude Code**, **Codex CLI**, **GitHub Copilot**, **Hermes Agent** (Nous Research), **OpenClaw**, **Cursor**, **Aider** e qualquer outro agent que respeite o padrão `AGENTS.md`. É o contrato entre humano e IA neste repositório.
>
> Mudou algo aqui? Reflete em `CLAUDE.md` e `.github/copilot-instructions.md` (mantém os três alinhados ou usa symlink).

Este arquivo dá ao agent **tudo que ele precisa saber pra entregar uma task** sem perguntar: stack, comandos, fluxo de trabalho, padrões, proibições, skills disponíveis e atalhos. Lê ele inteiro antes de escrever a primeira linha de código.

---

## Stack

Painel local single-user pra triagem de bookmarks de x.com. Roda só em `127.0.0.1`. macOS only por hoje.

- Linguagem principal: **Python 3.11+**
- Framework web/API: **Flask 3.0+** (única dep do hot path, ver `server/requirements.txt`)
- Banco de dados: **SQLite** via `sqlite3` stdlib, arquivo em `data/bookmarks.db`
- Frontend: HTML + CSS + **vanilla JS** em `index.html` (893 linhas, sem build, sem bundler)
- Runtime always-on: **launchd** (panel + watchdog) — `scripts/launchd/*.plist.template`
- Integrações macOS: `pbcopy`, `osascript`/`Terminal.app`, `open -a` (app Claude desktop), `git`, `gh`
- Test runner unit: **TODO** — sem suíte de teste hoje (item #3 do `.specs/sprints/BACKLOG.md`)
- Linter/formatter: **TODO** — não há config hoje
- CI/CD: **TODO** — `.github/workflows/` ainda sem pipeline real (item #2 do BACKLOG)
- Deploy: não aplicável — local-first, instalação via `./setup.sh` + `./install-launchd.sh`

> Antes de adicionar dependência nova: **pergunta ao usuário**. Sem exceção.

---

## Comandos importantes

```bash
# setup (idempotente — pode rodar 1 ou 100 vezes)
./setup.sh                                # cria venv, instala Flask, copia .env.example -> .env
./install-launchd.sh                      # registra panel + watchdog em ~/Library/LaunchAgents/

# desenvolvimento (foreground, debug)
./start.sh                                # ativa venv + python server/app.py em :8765
python server/app.py                      # alternativa direta (precisa venv ativo)
./stop.sh                                 # mata processo + descarrega launchd se ativo

# inspecionar dados
sqlite3 data/bookmarks.db ".tables"
sqlite3 data/bookmarks.db "SELECT id, link, status FROM oportunidades LIMIT 10;"

# logs (capturados pelo launchd)
tail -f data/panel.out.log                # stdout do Flask
tail -f data/panel.err.log                # stderr / stack traces
tail -f data/healthcheck.log              # watchdog (a cada 5min)

# always-on (launchd)
launchctl list | grep com.bookmarks       # status dos agents
./healthcheck.sh                          # roda watchdog manual (curl /api/healthz)

# smoke test endpoints
curl -s http://localhost:8765/api/healthz
curl -s http://localhost:8765/api/oportunidades | jq '.[] | {id, status, prioridade}'

# qualidade
# TODO: pytest + ruff + black ainda não configurados (BACKLOG #2 e #3)

# git/PR
git checkout -b feat/<slug>
gh pr create --fill                       # usa template padrão se existir
gh run watch                              # acompanha CI quando workflow estiver pronto
```

Sem `npm`, sem `npx`, sem `dotnet` aqui. É Python + shell + SQLite, ponto.

---

## Workflow loop OBRIGATÓRIO

Toda task técnica passa por esses passos. Não pula etapa.

1. **Ler task** — abre arquivo em `.specs/sprints/sprint-XX/<task-id>.task.md`. Lê contexto + acceptance criteria + test plan + DoD.
2. **Planejar** — escreve plano interno curto: o que muda, quais arquivos, como verificar, efeitos colaterais. Se task ambígua → pergunta antes de codar.
3. **Carregar contexto** — lê `.specs/architecture/PATTERNS.md` + ADRs relevantes em `.specs/architecture/ADR-*.md`. Verifica skills aplicáveis em `.skills/`.
4. **Editar** — aplica edits cirúrgicos. Só toca o que a task pede. Sem refactor extra, sem renomeação, sem comentário a mais.
5. **Lint** — `npm run lint`. Vermelho = corrige antes de seguir.
6. **Unit** — `npm test`. Vermelho = corrige antes de seguir. Coverage do diff >= 80%.
7. **E2E** — `npx playwright test`. Captura screenshot/trace/video. Vermelho = corrige.
8. **Fix loop** — se qualquer etapa falhou: volta ao passo 4. Repete até verde.
9. **Commit** — Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`). Mensagem em **inglês**. Body explica *why*, não *what*.
10. **PR** — `gh pr create`. Preenche template inteiro: link da task, evidências (screenshots Playwright), checklist DoD marcado.

---

## Definition of Done

PR só faz merge quando **todos** os itens abaixo estão marcados:

- [ ] Unit tests passam (`npm test` verde)
- [ ] Lint passa (`npm run lint` verde)
- [ ] E2E Playwright passa com **evidência anexada** (screenshot, trace ou video em `playwright-report/`)
- [ ] Coverage do diff >= 80%
- [ ] Acceptance Criteria da task: todos os checkboxes marcados
- [ ] PR template preenchido (link task + descrição + evidências)
- [ ] Conventional commit no merge
- [ ] ADR criado em `.specs/architecture/` se mudou decisão arquitetural
- [ ] Changelog atualizado se release-relevant
- [ ] Sem warning novo no console
- [ ] Sem `console.log` / `print` / `Debug.WriteLine` deixado pra trás
- [ ] Sem TODO sem dono e sem prazo

CI bloqueia merge se DoD falhar (`.github/workflows/dod.yml`).

---

## Padrões de código

Padrões completos em `.specs/architecture/PATTERNS.md`. Resumo:

- Naming, estrutura de pastas, criação de endpoint/componente/teste, tratamento de erro, logging, validação — **tudo lá**.
- Decisões irreversíveis viram **ADR** em `.specs/architecture/ADR-XXX-*.md` (template em `.specs/architecture/ADR-template.md`).
- Antes de escrever código novo: lê `PATTERNS.md` da seção relevante. Não inventa estilo próprio.

---

## Onde encontrar contexto

| Pergunta | Onde olha |
|---|---|
| Por que esse produto existe? | `.specs/product/VISION.md` |
| Quem é o usuário? | `.specs/product/PERSONAS.md` |
| Quais entidades de negócio? | `.specs/product/DOMAIN.md` |
| Como o sistema é desenhado? | `.specs/architecture/DESIGN.md` |
| Como escrever código aqui? | `.specs/architecture/PATTERNS.md` |
| Por que decidimos X? | `.specs/architecture/ADR-*.md` |
| Como faço PR/branch/release? | `.specs/workflow/WORKFLOW.md`, `RELEASE.md`, `CONTRIBUTING.md` |
| O que tá no backlog? | `.specs/sprints/BACKLOG.md` |
| Sprint atual? | `.specs/sprints/sprint-XX/SPRINT.md` |
| Tasks abertas? | `.specs/sprints/sprint-XX/*.task.md` |
| Skills/capacidades reutilizáveis? | `.skills/README.md` + `.skills/*/SKILL.md` |

---

## Proibido

Lista negra. Nada aqui é negociável.

- **Pular testes** — sem unit/E2E = sem merge.
- **Mockar pra fazer passar** — mock só pra isolar dependência externa real (HTTP, DB), nunca pra esconder falha.
- **Commit com vermelho** — lint/test falhando = não commita. Hook `.claude/hooks/pre-commit.sh` bloqueia.
- **Ignorar ADR** — decisão registrada em ADR é lei. Reverter/mudar ADR exige novo ADR ("Supersedes ADR-XXX").
- **Adicionar dependência sem perguntar** — toda nova dep (`npm install`, `dotnet add`, etc.) passa por confirmação humana.
- **Editar arquivo não lido** — lê antes de editar. Sempre.
- **Refactor escondido em PR de feature** — refactor = PR separado.
- **Force push em `main`/`master`** — bloqueado por hook e por settings do repo.
- **Commitar segredo** — `.env`, token, key, senha → nunca. Usa `.gitignore` + secrets manager.
- **Reformatar arquivo inteiro num PR pequeno** — diff polui review.

---

## Skills disponíveis

Skills moram em `.skills/<nome>/SKILL.md` e são capacidades reutilizáveis que o agent invoca quando o trigger casa. Lista atual:

- **`playwright-e2e`** — como escrever teste Playwright neste projeto. Trigger: nova feature de UI ou fluxo end-to-end. Cobre fixtures, page objects, evidências (trace/screenshot/video) e padrões de assert.
- **`conventional-commits`** — regras de commit (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `perf:`, `style:`, `ci:`, `build:`). Trigger: hora de commitar. Inclui exemplos, breaking changes (`!`/`BREAKING CHANGE:`) e scope.
- **`_template`** — base pra criar skill nova. Copia, renomeia pasta, preenche frontmatter (`name`, `description`, `trigger`, `steps`, `dod`).

Detalhes completos: `.skills/README.md`.

---

## Comandos especiais

### Criar nova ADR

```bash
# encontra proximo numero
ls .specs/architecture/ADR-*.md | tail -1
# copia template
cp .specs/architecture/ADR-template.md .specs/architecture/ADR-XXX-<slug>.md
# edita: Status, Contexto, Decisao, Consequencias, Alternativas
# commita junto com a feature que motivou a decisao
```

### Abrir PR

```bash
git push -u origin $(git branch --show-current)
gh pr create --fill        # usa template padrao (.github/PULL_REQUEST_TEMPLATE.md)
gh pr view --web           # abre no browser pra revisar
gh run watch               # acompanha CI
```

### Criar task nova

```bash
cp .specs/sprints/task-template.md .specs/sprints/sprint-XX/<id>-<slug>.task.md
# preenche: Contexto, Acceptance Criteria, Out of scope, Test plan, DoD, Pegadinhas, Links
# adiciona linha em .specs/sprints/BACKLOG.md
```

### Criar skill nova

```bash
cp -R .skills/_template .skills/<nome-da-skill>
# edita SKILL.md: name, description, trigger, steps, padroes, DoD
# referencia em .skills/README.md
```

### Rodar checklist DoD localmente antes de PR

```bash
npm run lint && npm test -- --coverage && npx playwright test
# se tudo verde -> git commit && git push && gh pr create --fill
```

---

## Notas finais pro agent

- **Idioma**: respostas/docs em **pt-BR**, código (vars/funções/classes) em **inglês**, commits em **inglês**.
- **Sem emoji em código**. README/slides ok.
- **Sem resumo no final** de uma resposta. Entrega o trabalho e finaliza.
- **Sem estimativa de tempo** (não tem como prever, não promete).
- **Pergunta apenas em ambiguidade real** do pedido. Não pergunta pra confirmar trabalho de execução.
- **Paralelo é o padrão** — research + read + review independentes rodam simultâneos.
- **Hooks do `.claude/hooks/`** rodam automaticamente: post-edit faz lint/format, pre-commit bloqueia commit vermelho.

<!-- codex-long-running-agent-overlay:start -->
## Universal Long-Running Agent Overlay

This section complements the repository-specific guidance already in this file. If anything here conflicts with the repo-specific rules above, the repo-specific rules win.

- `PRD.md` is the task source of truth for long-running sessions.
- `PROGRESS.md` is the persistent checkpoint log.
- `GOAL_RESULT.md` is the final execution report.
- Before coding, read this file, `PRD.md`, `PROGRESS.md` when it exists, `README.md`, project manifests, tests, and the relevant source folders.
- Work in small checkpoints, run the smallest relevant validation after each meaningful change, update `PROGRESS.md`, and continue until complete or genuinely blocked.
- Stop only when the requested work is complete, validation is documented, and `GOAL_RESULT.md` reflects the outcome.
- Do not rewrite unrelated architecture, fake successful validation, expose secrets, or push without explicit operator instruction for the active session.
<!-- codex-long-running-agent-overlay:end -->

Use o repo canonico https://github.com/wesleysimplicio/yool-tuple-hamt. 
Leia antes de editar: YOOL_TUPLE_HAMT.md, kernel/yool_tuple_kernel.py,
guardrails/cpu_throttle.py, guardrails/disk_gc.py, examples/python/receipts.py
e scripts/build_hamt.py.

Ao receber "Implement X": decomponha em grafo Hilbert-indexed, crie tuple raiz,
use batch_spawn(depth, branching, compression_threshold) para 1.000.000+
subagents sem enumerar, execute work ativo com spawn_agent, roteie por out/in/rd,
route_packet e scan_index, aplique hookwall, compress_token e prune_idle, e use
LaneWorkerPool respeitando YOOL_TUPLE_* env vars.

Execute:
python kernel/yool_tuple_kernel.py

Responda SEMPRE exatamente neste formato (sem varia??es):
[Tuple Space Snapshot] 
[Active Agents/Subagents]
[Total Agents/Subagents]
[Pr?ximo Yool a executar]
[Resultado parcial]
