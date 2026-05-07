# Copilot Instructions

> Instruction file lido automaticamente pelo **GitHub Copilot Chat** e **Copilot Workspace / Agent Mode**. Espelha [AGENTS.md](../AGENTS.md) com foco em **Agent Mode workflow**.
>
> Ao trabalhar em Agent Mode, o Copilot pode delegar pra custom agents em `.github/copilot/*.agent.md`. Lista atual: `tdd.agent.md`, `reviewer.agent.md`, `architect.agent.md`.

---

## Stack

Painel local single-user pra triagem de bookmarks de x.com. Bind em `127.0.0.1`. macOS only por hoje.

- Linguagem principal: **Python 3.11+**
- Framework web/API: **Flask 3.0+** (única dep, `server/requirements.txt`)
- Banco de dados: **SQLite** via `sqlite3` stdlib, arquivo `data/bookmarks.db`
- Frontend: vanilla JS em `index.html` (sem build, sem bundler)
- Runtime always-on: **launchd** (panel + watchdog) em `scripts/launchd/*.plist.template`
- Integrações macOS: `pbcopy`, `osascript`/`Terminal.app`, `open -a`, `git`, `gh`
- Test runner: **TODO** — sem suíte hoje (BACKLOG #3)
- Linter/formatter: **TODO** — sem config hoje
- CI/CD: **TODO** — `.github/workflows/` ainda sem pipeline (BACKLOG #2)
- Deploy: não aplicável — local-first via `./setup.sh` + `./install-launchd.sh`

> Antes de adicionar dependência nova: pergunta ao humano. Sem exceção.

---

## Comandos importantes

```bash
# setup (idempotente)
./setup.sh                                # venv + Flask + .env
./install-launchd.sh                      # registra panel + watchdog

# desenvolvimento
./start.sh                                # foreground em :8765
python server/app.py                      # alternativa direta
./stop.sh                                 # mata + descarrega launchd

# inspecionar dados
sqlite3 data/bookmarks.db ".tables"
sqlite3 data/bookmarks.db "SELECT id, link, status FROM oportunidades LIMIT 10;"

# logs (captura via launchd)
tail -f data/panel.out.log
tail -f data/panel.err.log
tail -f data/healthcheck.log

# always-on
launchctl list | grep com.bookmarks
./healthcheck.sh

# smoke
curl -s http://localhost:8765/api/healthz
curl -s http://localhost:8765/api/oportunidades | jq '.[] | {id, status, prioridade}'

# git/PR
git checkout -b feat/<slug>
gh pr create --fill
gh run watch
```

Sem `npm`, sem `npx`, sem `dotnet`. É Python + shell + SQLite.

---

## Workflow loop OBRIGATÓRIO (Agent Mode)

Em Copilot Workspace/Agent Mode, todo plano de execução segue esse loop. Não pula etapa.

1. **Ler task** — abre `.specs/sprints/sprint-XX/<task-id>.task.md`. Lê contexto + acceptance criteria + test plan + DoD.
2. **Plano explícito** — Copilot Workspace gera spec/plan. Revisa antes de implementar.
3. **Carregar contexto** — `.specs/architecture/PATTERNS.md` + ADRs relevantes em `.specs/architecture/ADR-*.md`. Skills aplicáveis em `.skills/`.
4. **Implementar (Agent Mode)** — edits cirúrgicos. Só toca o que a task pede. Sem refactor extra.
5. **Lint** — `npm run lint`. Vermelho = corrige.
6. **Unit** — `npm test`. Vermelho = corrige. Coverage do diff >= 80%.
7. **E2E** — `npx playwright test`. Captura screenshot/trace/video.
8. **Fix loop** — falhou? Volta ao 4. Repete até verde.
9. **Commit** — Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`). Mensagem em **inglês**.
10. **PR** — `gh pr create --fill`. Preenche template inteiro.

---

## Definition of Done

PR só faz merge quando todos os itens abaixo estão marcados:

- [ ] Unit tests passam
- [ ] Lint passa
- [ ] E2E Playwright passa **com evidência anexada** (screenshot, trace, video)
- [ ] Coverage do diff >= 80%
- [ ] Acceptance Criteria todos marcados
- [ ] PR template preenchido (link task + descrição + evidências)
- [ ] Conventional commit no merge
- [ ] ADR criado se mudou decisão arquitetural
- [ ] Changelog atualizado se release-relevant
- [ ] Sem warning novo, sem `console.log`/`print` deixado pra trás
- [ ] Sem TODO sem dono e sem prazo

CI bloqueia merge se DoD falhar (`.github/workflows/dod.yml`).

---

## Padrões de código

`.specs/architecture/PATTERNS.md` é a **fonte única**. Naming, estrutura, criação de endpoint/componente/teste, tratamento de erro, logging, validação — tudo lá.

Decisões irreversíveis viram **ADR** em `.specs/architecture/ADR-XXX-*.md` (template em `.specs/architecture/ADR-template.md`).

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
| Backlog? | `.specs/sprints/BACKLOG.md` |
| Sprint atual? | `.specs/sprints/sprint-XX/SPRINT.md` |
| Skills? | `.skills/README.md` + `.skills/*/SKILL.md` |

---

## Proibido

- **Pular testes** — sem unit/E2E = sem merge.
- **Mockar pra fazer passar** — mock só pra dep externa real (HTTP, DB), nunca pra esconder falha.
- **Commit com vermelho** — lint/test falhando = não commita.
- **Ignorar ADR** — decisão registrada é lei.
- **Adicionar dependência sem perguntar.**
- **Editar arquivo não lido.**
- **Refactor escondido em PR de feature** — PR separado.
- **Force push em `main`/`master`.**
- **Commitar segredo** (`.env`, token, key, senha).
- **Reformatar arquivo inteiro num PR pequeno.**

---

## Custom agents (Copilot Workspace / Agent Mode)

Copilot pode delegar pra um custom agent quando a tarefa casa com a `description` do agent. Definidos em `.github/copilot/`:

- **`tdd.agent.md`** — TDD Specialist. Escreve teste falhando antes do código. Loop red-green-refactor. Tools: `edit`, `terminal`, `search`. Aciona quando tarefa exige cobertura nova ou regression test.
- **`reviewer.agent.md`** — Code Reviewer. Read-only. Comenta problemas e sugestões em PR. Tools: `search`, `read`. Aciona em revisão de PR aberto, sem editar arquivos.
- **`architect.agent.md`** — Architect. Desenha arquitetura, cria ADRs, atualiza `PATTERNS.md`. **Não escreve código de produção.** Tools: `edit`, `search`, `read`. Aciona em decisão arquitetural, refactor amplo, integração nova.

Pra invocar explicitamente em Copilot Chat: `@tdd`, `@reviewer`, `@architect`.

---

## Skills disponíveis (`.skills/`)

- **`playwright-e2e`** — como escrever teste Playwright. Trigger: nova feature de UI / fluxo end-to-end.
- **`conventional-commits`** — regras de commit (`feat:`, `fix:`, etc.). Trigger: hora de commitar.
- **`_template`** — base pra criar skill nova.

Detalhes em `.skills/README.md`.

---

## Comandos especiais

### Criar nova ADR

```bash
cp .specs/architecture/ADR-template.md .specs/architecture/ADR-XXX-<slug>.md
# preenche e commita junto com a feature
```

### Abrir PR

```bash
git push -u origin $(git branch --show-current)
gh pr create --fill
```

### Criar task

```bash
cp .specs/sprints/task-template.md .specs/sprints/sprint-XX/<id>-<slug>.task.md
```

### DoD local antes de push

```bash
npm run lint && npm test -- --coverage && npx playwright test
```

---

## Notas finais

- **Idioma**: docs em pt-BR, código em inglês, commits em inglês.
- **Sem emoji em código fonte.** README/slides ok.
- **Sem resumo no final** de resposta.
- **Sem estimativa de tempo.**
- **Pergunta apenas em ambiguidade real.**
- **Paralelismo** — research + read + review independentes rodam simultâneos em Agent Mode.
