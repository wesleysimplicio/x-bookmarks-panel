# PERSONAS — bookmarks-oss

Quem usa o painel. O produto é local-first single-user (binda em `127.0.0.1`, sem auth) — então só faz sentido descrever o humano que rodou `./setup.sh` e o agente IA que ele dispara via botão **Execute**.

> Regra: feature que não move uma destas personas não entra. Multi-tenant, RBAC e SSO estão explicitamente fora — ver `VISION.md` seção "Não-objetivos".

---

## Persona 1 — Dev solo / founder técnico (primária)

**Arquétipo:** desenvolvedor solo no macOS que usa X como entrada de inspiração técnica.

### Quem é

- **Papel/profissão:** indie hacker, founder técnico, consultor que entrega código sozinho.
- **Plataforma:** macOS (depende de `launchctl`, `pbcopy`, `osascript`, AppleScript). Linux/Windows fora.
- **Familiaridade com tech:** alta — terminal, git, brew, gh, Claude Code instalados.
- **Familiaridade com IA:** alta — já usa Claude Code (CLI) e o app desktop Claude (Cowork) na rotina.

### Objetivos

- Transformar bookmark salvo às 23h em commit antes de esquecer.
- Reduzir para uma click o caminho do tweet → pasta de projeto com `git init` + `gh repo create`.
- Decidir rápido: `agir-agora`, `estudar-depois` ou `arquivar`.
- Não pagar por SaaS de read-it-later, não vazar dado para nuvem.

### Frustrações / dores

- Bookmarks no X viram cemitério: salva, scroll, esquece.
- Read-it-later (Pocket/Raindrop) arquiva mas não executa.
- Gestor de tarefas (Linear/Things) não conhece o contexto do tweet.
- Cada projeto novo: 5 minutos de setup repetitivo (mkdir, README, `git init`, `gh repo create`).

### Contexto de uso

- **Ambiente:** Terminal.app + browser + app Claude desktop. Painel rodando 24/7 em `localhost:8765` via launchd.
- **Frequência:** abre o painel 1-3x por dia, em janela curta (5-15min).
- **Sessão típica:** olhar `agir-agora`, clicar **Execute** em 1-3 cards, voltar à rotina.
- **Trigger principal:** novo HTML curado virou import; ou sentou para "limpar a fila".

### Métrica que importa

- Tempo entre import e primeira execução (`MIN(execucoes.started_at) - oportunidades.created_at`) — meta: < 24h para `agir-agora`.
- Razão `executado / total` por mês (via `db.stats()`).
- Projetos com `github_url` ativo (`projetos` onde `github_url IS NOT NULL`).

---

## Persona 2 — Agente IA convocado dentro de um projeto gerado (secundária)

**Arquétipo:** Claude Code (ou outro agent compatível com `CLAUDE.md`) invocado **dentro** de uma pasta criada pelo botão **+ New project**.

### Quem é

- Não-humano. Lê `README.md` + `CLAUDE.md` que `executor.criar_projeto` plantou na pasta.
- Cada pasta `<repo>/<slug>/` tem o próprio `git`, próprio `CLAUDE.md`, próprio escopo.
- **Limitações:** janela de contexto, sem memória entre sessões, depende 100% do `CLAUDE.md` + `README.md` que o painel gerou.

### Objetivos

- Ler o contexto do bookmark (objetivo, insight, ação sugerida) sem perguntar nada ao humano.
- Escrever o primeiro commit que prove a ideia do tweet.
- Não confundir o `CLAUDE.md` da pasta gerada com o `CLAUDE.md` raiz do painel.

### Frustrações / dores

- Bookmark vago vira `acao_sugerida` vaga vira prompt vago.
- Falta dependência mencionada no tweet (`instalado=0`) — agente não sabe e gasta tokens tentando.
- `CLAUDE.md` gerado sem invariantes claras leva a refactor sem objetivo.

### Contexto de uso

- **Ambiente:** dentro de `<repo>/<slug>/`, disparado por `claude "<prompt>"` que `executor.executar` colou no Terminal.
- **Frequência:** uma sessão por execução; pode reabrir manualmente depois.
- **Trigger principal:** clipboard tem o prompt, Terminal abriu na pasta, agent começa lendo `CLAUDE.md`.

### Métrica que importa

- Sessão termina com commit? (sucesso) vs sessão termina sem commit? (prompt vago ou contexto faltando).
- `execucoes.status` vira `concluida` ou fica preso em `iniciada`?

---

## Quem NÃO é o público

Documenta as exclusões para não vir feature errada.

- **Times grandes / multi-tenant:** sem auth, sem RBAC, sem org. `127.0.0.1` é hard-coded por design.
- **Usuários sem macOS:** Linux está no roadmap (`README.md`), Windows não está.
- **Usuários sem Claude Code instalado:** painel funciona, mas o botão **Execute** é o ponto central — sem CLI, vira só read-it-later.
- **Quem quer triagem automática:** o painel **consome** HTML curado; não opina sobre como o HTML nasce. Pipeline de triagem (manual, scraper, agente externo) é responsabilidade de fora.

---

## Histórico

| Data | Versão | Mudança | Quem |
|---|---|---|---|
| 2026-05-07 | 0.1 | Criação inicial — duas personas reais (dev solo + agente IA convocado), exclusões explícitas | Wesley Simplicio |
