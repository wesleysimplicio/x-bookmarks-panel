# BACKLOG — bookmarks-oss

Lista priorizada do que falta. Fonte da verdade de pendências. Cada linha vira `task.md` quando entra em sprint.

> **Nota factual:** `grep -rn "TODO\|FIXME" server/ index.html *.sh README.md` em `2026-05-07` voltou **vazio** — não há TODO/FIXME deixados no código. Os itens abaixo vêm de:
> 1. Roadmap declarado em `README.md` linhas 222-228 (5 itens).
> 2. Débitos óbvios observados pelo agente na varredura inicial (testes, CI, ADRs faltantes, divergências de placeholder).
> 3. `gh issue list` — nenhuma issue aberta (repo ainda não publicado ou sem issues registradas).

## Como usar

- Cada linha é rastreável e vira `sprint-XX/<id>-<slug>.task.md` quando puxada.
- Prioridades:
  - **P0** — bloqueia release ou cria risco real (segurança, dado perdido, painel quebrado).
  - **P1** — importante, próximas 1-2 sprints.
  - **P2** — desejável, fica no radar.
- Status: `todo` / `doing` / `done`.
- Ordenação: P0 → P1 → P2; dentro do mesmo nível por sprint alvo.

## Regras de manutenção

- Toda ideia nova entra como P2 até alguém defender priorizar.
- Item `done` fica uma sprint no histórico, depois move para `BACKLOG-archive.md`.
- Item `todo` por 2 sprints sem mover: reavalia ou descarta.
- Quem altera prioridade ou move para `doing` atualiza esta tabela no mesmo PR.

## Backlog atual

| # | Título | Prioridade | Sprint alvo | Status | Origem |
|---|---|---|---|---|---|
| 1 | Atualizar `.starter-meta.json` (campo `stack` está como `dotnet`, real é Python/Flask) | P0 | sprint-01 | todo | divergência observada (`.starter-meta.json:5`) |
| 2 | Pipeline CI mínimo (`.github/workflows/ci.yml`): `pip install -r server/requirements.txt` + lint Python + smoke `python server/app.py --check` | P0 | sprint-01 | todo | sem CI hoje |
| 3 | Suíte de testes inicial (`pytest`) cobrindo `db.upsert_oportunidade`, `db.migrate`, `executor.heuristic_tipo`, `importer.extract_bookmarks_array` | P0 | sprint-01 | todo | sem testes hoje |
| 4 | ADR-002: bind em `127.0.0.1` sem auth — risco aceito, condição para flipar para `0.0.0.0` | P1 | sprint-02 | todo | DESIGN.md seção 5 |
| 5 | ADR-003: schema pt-BR vs identifiers em inglês — quando renomear, quando manter | P1 | sprint-02 | todo | DESIGN.md seção 5 |
| 6 | ADR-004: launchd como única estratégia always-on (não cron, não systemd) — caminho para Linux | P1 | sprint-02 | todo | DESIGN.md seção 5 |
| 7 | Filterable execution history na UI (filtros por `tipo`, `status`, intervalo de data) | P1 | sprint-03 | todo | README.md:224 |
| 8 | Webhook que reimporta quando o pipeline externo de triagem roda (em vez de polling/manual) | P1 | sprint-03 | todo | README.md:225 |
| 9 | Endpoint `POST /api/projetos/<id>/abrir` para reabrir Claude Code numa pasta scaffold existente | P1 | sprint-03 | todo | README.md:226 |
| 10 | Exportação CSV/JSON dos bookmarks (`GET /api/oportunidades.csv`, `GET /api/oportunidades.json`) | P2 | sprint-04 | todo | README.md:227 |
| 11 | Linux support — substituir `pbcopy` (xclip/wl-copy), AppleScript (xterm/gnome-terminal), `launchctl` (systemd user units) | P2 | sprint-05 | todo | README.md:228 + DESIGN.md seção 7 |
| 12 | Healthcheck mais granular: `/api/healthz` retornando contadores por status + última execução com sucesso | P2 | backlog | todo | observado em DESIGN.md seção 8 |
| 13 | Métricas reais para `VISION.md` (preencher os `TODO: humano preencher` em baseline + meta) | P2 | backlog | todo | VISION.md tabela seção "Métricas" |

## Histórico recente

| # | Título | Sprint | Concluído em |
|---|---|---|---|
| 0 | Bootstrap inicial — `.specs/`, `.skills/`, `.claude/`, `.codex/`, `.github/` criados via `bootstrap.sh` | sprint-00 | 2026-05-07 |

## Itens descartados

Nenhum até agora.

## Decisões pendentes (precisam de produto/arquitetura antes de virar task formal)

- Webhook do item #8: qual segredo, onde guarda (`.env` ou Keychain), como invalidar.
- CSV/JSON export do #10: incluir conteúdo cru dos bookmarks ou só metadados? Política de PII.
- Linux do #11: trade-off entre fork de plataforma e abstração `platform.adapter` (pode virar ADR antes da task).
- Política de retenção de `data/panel.{out,err}.log` e `data/healthcheck.log` (cresce sem rotate hoje).
