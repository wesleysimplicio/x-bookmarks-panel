# VISION — bookmarks-oss

> Painel local que transforma bookmarks salvos no x.com em fila acionável de tarefas. Local-first, sem telemetria, sem token externo.

---

## Problema

Bookmarks no X viram cemitério: você salva um tweet jurando voltar, e ele some no scroll. Não há triagem, não há cobrança, não há ponte com a ferramenta que de fato vai executar (Claude Code, app Claude desktop, browser).

- **Quem sente:** desenvolvedor solo / consultor que usa X como entrada de inspiração técnica e produto.
- **Custo:** horas de scroll buscando aquele tweet, ideias que não viram código, contexto perdido entre sessões.
- **Por que ferramentas existentes não resolvem:** read-it-later (Pocket, Raindrop) arquiva, não executa; gestor de tarefas (Linear, Things) não conhece o contexto do tweet original.

---

## Quem usa

Resumo das personas. Detalhes em [`PERSONAS.md`](./PERSONAS.md).

- **Persona primária:** desenvolvedor solo / founder técnico que opera no macOS, já tem Claude Code e (opcional) `gh` instalados.
- **Persona secundária:** agente IA invocado dentro de uma pasta criada pelo botão **+ New project**, que recebe contexto do bookmark via `README.md` e `CLAUDE.md` gerados.
- **Quem NÃO é o público:** times grandes com fluxo multi-usuário, usuários sem macOS, qualquer cenário com necessidade de auth/multi-tenant.

---

## Diferencial

- **Local-first absoluto:** binda em `127.0.0.1`, zero telemetria, zero credencial em repo, SQLite em disco.
- **Forçar decisão:** cada card sai do limbo via uma de três rotas — `agir-agora`, `estudar-depois`, `arquivar`.
- **Ponte direta com o executor certo:** heurística (`server/executor.py:65-82`) + override classifica entre Claude Code (tarefa de código) e Cowork/app Claude desktop (tarefa visual), copia o prompt no clipboard e abre o app.
- **Scaffold de projeto em um clique:** `+ New project` cria pasta, `README.md` + `CLAUDE.md` com contexto do bookmark, `git init`, commit inicial e (opcional) `gh repo create --private`.
- **Sempre online:** dois agents launchd — painel + watchdog que pinga `/api/healthz` a cada 5 min e dá `kickstart -k` se cair.

---

## Métricas de sucesso

| Métrica | Baseline | Meta (3 meses) | Como medimos |
|---|---|---|---|
| Bookmarks que viram ação executada | TODO: humano preencher | TODO: humano preencher | `db.stats().executado` / `db.stats().total` |
| Tempo entre import e primeira execução | TODO: humano preencher | TODO: humano preencher | `MIN(execucoes.started_at) - oportunidades.created_at` |
| Projetos com `github_url` ativo | TODO: humano preencher | TODO: humano preencher | `count(projetos.github_url IS NOT NULL)` |
| Uptime do painel | TODO: humano preencher | >= 99% | `data/healthcheck.log` |

---

## Não-objetivos

- **Não somos read-it-later.** Quem quer só guardar tweet usa Pocket ou favoritos do navegador.
- **Não somos gestor de tarefas multi-usuário.** Tudo binda em `127.0.0.1`, sem auth, sem RBAC.
- **Não suportamos Linux/Windows hoje.** Depende de `launchctl`, `pbcopy`, AppleScript. Linux está no roadmap (README.md).
- **Não geramos código pelo painel.** O painel apenas dispara Claude Code/Cowork; quem escreve é o agente que abre.
- **Não substituímos triagem manual ou agente externo de curadoria.** O painel consome um HTML produzido por qualquer pipeline — não opina sobre como o HTML nasce.

---

## Tese de longo prazo

Em 12 meses, qualquer dev que salve um bookmark no X tem caminho de uma click do tweet ao primeiro commit do projeto que o tweet inspirou — sem cair em ferramenta nova, sem token externo, sem perder contexto.

---

## Histórico

| Data | Versão | Mudança | Quem |
|---|---|---|---|
| 2026-05-07 | 0.2 | Reescrita pós-bootstrap baseada em README/server real | Wesley Simplicio |
| 2026-05-07 | 0.1 | Criação inicial via starter | Wesley Simplicio |
