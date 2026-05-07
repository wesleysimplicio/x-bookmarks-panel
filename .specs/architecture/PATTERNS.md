# PATTERNS — bookmarks-oss

> Como escrever código aqui. Curto, opinativo, executável.
> Audiência: dev humano e agent AI. Padrões observados no código real (`server/*.py`, `index.html`, scripts shell). Não inventa convenção que ninguém segue.

---

## 1. Naming

| Item | Convenção | Exemplo bom (existe no repo) | Exemplo ruim |
|---|---|---|---|
| Funções/variáveis Python | `snake_case` em **inglês** | `upsert_oportunidade`, `heuristic_tipo`, `gerar_slug_para` | `Salvar`, `getStatus` |
| Identificadores pt-BR mantidos por compat | manter como está | `oportunidade`, `executar`, `acao_sugerida`, `tipo_execucao`, `vale_executar` | renomear sem ADR |
| Classes Python | `PascalCase` | (não há classes públicas hoje; helpers são funções) | — |
| Arquivos Python | `snake_case.py` | `app.py`, `db.py`, `executor.py`, `importer.py` | `App.py` |
| Scripts shell | `kebab-case.sh` ou nome curto | `setup.sh`, `install-launchd.sh`, `healthcheck.sh` | `Setup.sh` |
| Templates launchd | `.plist.template`, placeholders `__NOME__` | `panel.plist.template`, `__LABEL__`, `__REPO__`, `__PORT__` | template com valores hard-coded |
| Branches | `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>` | `feat/import-webhook` | `wesley-stuff` |
| Commits | Conventional Commits, **inglês** | `feat: add execution log filter` | `update stuff` |
| Endpoints REST | `/api/<recurso>[/<id>][/<acao>]` | `/api/oportunidades/<id>/executar` | `/doExecution?id=1` |

Regra de ouro: **nome conta o quê, não o como**. Nomes pt-BR no schema/payload ficam por compat — não misturar inglês novo com pt-BR no mesmo registro.

---

## 2. Estrutura de pastas

Estrutura real, validada com `wc -l` em `2026-05-07`:

```
.
├── server/
│   ├── app.py            # 143 linhas — Flask, 8 rotas
│   ├── db.py             # 300 linhas — SCHEMA + helpers + migrate()
│   ├── executor.py       # 478 linhas — heurística, prompt, scaffold, side effects macOS
│   ├── importer.py       # 85 linhas — regex `const BOOKMARKS = [...]` -> upsert
│   └── requirements.txt
├── index.html            # 893 linhas — single-page, vanilla JS
├── scripts/launchd/
│   ├── panel.plist.template
│   └── watchdog.plist.template
├── examples/
│   └── sample-relatorio.html
├── data/                 # gitignored: bookmarks.db, panel.{out,err}.log, healthcheck.log
├── setup.sh              # 36 linhas — idempotente
├── start.sh              # 16 linhas — foreground, debug
├── stop.sh               # 37 linhas
├── install-launchd.sh    # 85 linhas — registra panel + watchdog
├── healthcheck.sh        # 47 linhas — invocado pelo plist a cada 5min
└── .env.example
```

Regra de import (Python): `app.py` importa de `db` e `executor` e `importer`. `db.py` é folha — não importa de mais nada do projeto. Quem cruza para fora (`pbcopy`, `git`, `gh`) é só `executor.py` via `subprocess`.

---

## 3. Como criar endpoint novo (Flask)

Passo a passo concreto:

1. Adicionar rota em `server/app.py` com `@app.route("/api/<recurso>", methods=[...])`. Mantém prefixo `/api/`.
2. Validar `request.get_json(silent=True) or {}` no topo do handler. Campo faltando = `400` com `{"error": "..."}`.
3. Para feature de domínio, adicionar helper em `server/db.py` (ex.: `list_filtros`, `update_oportunidade`). Sem SQL inline em `app.py`.
4. Se chama processo macOS (`pbcopy`, `osascript`, `git`, `gh`), **passar pelo `server/executor.py`** — não chamar `subprocess` direto em `app.py`.
5. Decidir status code:
   - `200` com payload JSON em sucesso.
   - `400` para input ruim (JSON inválido, campo obrigatório vazio).
   - `404` quando `db.get_*` retorna `None`.
   - `409` para conflito (`link` UNIQUE violado vira retorno informativo, não 500).
   - `500` só para exceção inesperada (deixa estourar — Flask formata).
6. Logar com `print(...)`. O launchd captura em `data/panel.{out,err}.log`.
7. Atualizar `index.html` (fetch + `cardHTML` + handler `click`) para consumir o endpoint.
8. Smoke test manual: `curl -X POST http://localhost:8765/api/...`.

**Critério de feito:** happy path + um caminho de erro testado por curl.

---

## 4. Como adicionar campo editável numa oportunidade

Espelhar o mesmo nome em **3 lugares** (regra do `CLAUDE.md` raiz):

1. `server/db.py:migrate()` — adiciona coluna idempotente:
   ```python
   for col in ("instalado", "aplicado", "projeto_iniciado", "<NOVO_CAMPO>"):
       if col not in cols:
           conn.execute(f"ALTER TABLE oportunidades ADD COLUMN {col} INTEGER DEFAULT 0")
   ```
2. `server/app.py:api_update` — incluir o nome no `set` `allowed`.
3. `index.html` — adicionar à `cardHTML()` e ao handler `click` (`data-act="<acao>"`).

Se o campo é flag 0/1, manter o padrão `INTEGER DEFAULT 0` (consistente com `instalado`/`aplicado`/`projeto_iniciado`). Se é texto, sem `DEFAULT` ou `DEFAULT ''` conforme semântica.

---

## 5. Como adicionar heurística de classificação

`executor.py:heuristic_tipo` (linhas 65-82) decide entre `claude_code` e `cowork`. Para tunar:

1. Editar listas no topo do arquivo: `CODE_KEYWORDS`, `DESKTOP_KEYWORDS`, `CODE_CATEGORIES`, `DESKTOP_CATEGORIES`.
2. Espelhar a mesma lógica em `index.html` (função `recommendedTipo()`) — UI mostra a sugestão antes do clique. Heurística divergente entre back e front confunde.
3. Default histórico em empate ou nenhum match: cair para `cowork` (assume tarefa visual).

---

## 6. Tratamento de erro

Princípio: **falhar rápido em IO ruim, logar em IO opcional, nunca esconder exceção**.

- Input HTTP ruim: retorna `400` com `{"error": "<motivo>"}`. Sem stack trace pro cliente.
- Recurso ausente: `404` com `{"error": "oportunidade <id> não existe"}`.
- Processo macOS opcional falha (`gh` não autenticado, `pbcopy` ausente em SSH headless, app desktop fechado): **logar via `print` e seguir**. A request não morre. O painel registra `execucoes.status='iniciada'` mesmo assim — usuário vê e decide.
- Exceção inesperada: deixa estourar; Flask responde `500`. Não engolir com `try/except: pass`.
- `subprocess`: usar `subprocess.run([...], check=False, capture_output=True)`. Logar `stderr` se `returncode != 0`.

Sem `except: pass` em lugar nenhum. Se ignorar é decisão consciente, comentar o porquê em uma linha.

---

## 7. Logging

- Backend: `print(...)` simples. Stdout/stderr são capturados pelo launchd em `data/panel.out.log` e `data/panel.err.log`.
- Watchdog: `healthcheck.sh` escreve em `data/healthcheck.log`.
- **Não logar conteúdo cru** dos bookmarks (`texto`, `acao_sugerida`) — pode ser longo. Loga IDs (`op_id`), tipos, status.
- Sem framework de logging (Serilog, structlog) hoje. Adicionar = ADR.

---

## 8. Validação

- Validação acontece **na boundary HTTP** (`app.py`).
- JSON inválido / campo faltando: `400` antes de tocar `db` ou `executor`.
- CHECK constraints no SQLite (`prioridade`, `status`) protegem contra valor inválido como segunda linha de defesa — mas a primeira é o handler.
- Sem `pydantic`, sem `marshmallow` hoje. Validação manual com `if not body.get("foo"): return jsonify({"error": ...}), 400`.

---

## 9. Idempotência

Regra dura. Vale para todo script e import:

- `setup.sh` pode rodar 1 ou 100 vezes — copia `.env.example` só se faltar, cria venv só se faltar, instala Flask só se faltar.
- `install-launchd.sh` substitui placeholders `__LABEL__`/`__REPO__`/`__PORT__` no template, escreve em `~/Library/LaunchAgents/`, e dá `bootstrap`/`load` sem duplicar.
- `db.init_db()` + `db.migrate()` rodam toda vez que o app sobe — `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN` só se a coluna não existir.
- `importer.import_html()` faz upsert por `link`; re-import preserva `status`, `tipo_execucao`, `notas`, `instalado`, `aplicado`, `projeto_iniciado`.

---

## 10. Quando dividir vs manter junto

Limites práticos para este repo:

- **3 ocorrências da mesma lógica** = candidato a helper. Antes disso, copiar é OK.
- **Função > 50 linhas**: `executor.executar` e `criar_projeto` já beiram esse limite — split aceitável quando a função tem mais de uma responsabilidade clara.
- **Arquivo > 500 linhas**: `index.html` (893 linhas) é tolerado por ser SPA inteiro vanilla JS. Backend Python: split antes de chegar lá.
- **Sem framework no front**: não introduzir React/Vue/Svelte sem ADR. Vanilla é decisão arquitetural, não acidente.

Regra `Wesley Simplicio`: **simplicidade > elegância**. Código óbvio melhor que código esperto. 3 linhas repetidas melhor que abstração prematura.

---

## Histórico

| Data | Versão | Mudança | Quem |
|---|---|---|---|
| 2026-05-07 | 0.1 | Criação inicial — padrões observados em `server/*.py` real (não inventados) | Wesley Simplicio |
