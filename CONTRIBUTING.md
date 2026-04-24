# Contribuindo

Obrigado por querer contribuir. Algumas regras pra manter o projeto simples e legível.

## Antes de mandar PR

1. **Abra uma issue primeiro** se for mudança estrutural, adição de dependência nova, ou feature de escopo grande. Mudanças pequenas (typo, bug fix, edge case) podem vir direto como PR.
2. **Leia o [DESIGN.md](DESIGN.md)** pra entender o que foi intencionalmente excluído. Propostas pra adicionar ORM, framework frontend, auth ou deploy remoto serão fechadas (lidas, apreciadas, mas fechadas).
3. **Rode localmente**: `./setup.sh`, confirme que o painel sobe em `http://localhost:8765` e que `curl http://localhost:8765/api/healthz` devolve `{"ok": true}`.

## Convenções

- **Python**: PEP 8, f-strings, `pathlib`, `from __future__ import annotations`, type hints onde agregam.
- **Sem ORM.** SQLite direto em `server/db.py`.
- **Sem framework frontend.** HTML + fetch em `index.html`.
- **Comentários só quando o "por quê" não é óbvio no código.**
- **Idempotência** em tudo que toca o SO.
- **Commits** em inglês, imperativo, escopo curto: `feat: add export csv endpoint`, `fix: terminal escape when prompt has backticks`.

## Testando manualmente

O projeto ainda não tem suite automatizada. Smoke test mínimo antes de PR:

```bash
./stop.sh
rm -f data/bookmarks.db

./setup.sh
cp examples/sample-relatorio.html relatorio-bookmarks-x.html
curl -X POST http://localhost:8765/api/oportunidades/import
open http://localhost:8765

# Validações:
#   [ ] Painel abre e mostra 2 cards
#   [ ] Busca com "/" funciona
#   [ ] Filtros de prioridade/status/progresso reduzem os cards
#   [ ] Clicar "Claude Code" copia prompt pro clipboard (testa ⌘V em algum editor)
#   [ ] Clicar "+ Novo projeto" cria pasta em <repo>/<slug>/ e roda git init
#   [ ] Re-importar HTML preserva status/tipo_execucao/notas editados
```

## Escopo do projeto

**Dentro**: triagem local, UI simples, integração com Claude Code / Cowork / gh, launchd e sempre-online, SQLite.

**Fora**: multi-usuário, deploy remoto, auth, sincronização em nuvem, mobile app, scraping do próprio x.com (use a API oficial ou o pipeline de sua preferência pra gerar o HTML).

## Segurança

Se encontrar vulnerabilidade, **não abra issue pública**. Envie um e-mail para o autor (veja perfil GitHub). Foco em:

- Escape de prompt no `osascript` / `pbcopy`.
- Validação de path ao criar projetos (prevenir path traversal via `slug`).
- Qualquer vetor que permita RCE fora do cenário single-user esperado.

## Estilo de PR

- Um PR, um escopo. Se encontrar dois bugs, manda dois PRs.
- Descrição explica o **por quê** (não só o quê). Referencie a issue.
- Antes/depois: se muda UI, cola screenshot ou gif. Se muda API, mostra request/response.
- CHANGELOG.md recebe uma linha no topo de `[Unreleased]`.

Obrigado novamente — PRs bem descritos são metade do mérito.
