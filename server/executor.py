"""
Executor: triggers actions on the user's Mac.

Heuristic picks between two execution modes (manual override via API):
- Cowork  -> tasks requiring desktop/visual interaction (read article,
             browse UI, watch video, ad manager, etc.)
- Claude  -> code tasks (clone repo, install skill/plugin, scaffold a
             new project, edit settings.json, integrate an API, build MVP)

For Claude Code:
- Create folder `<root>/<slug>/` (or reuse existing)
- git init + README.md + CLAUDE.md with context
- (optional) gh repo create --private
- Open Terminal.app and run `cd <path> && claude "<prompt>"`

For Cowork (Claude desktop app):
- Put prompt on the clipboard via pbcopy
- Open the Claude app via `open -a "Claude"`
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import unicodedata
from pathlib import Path

import db

ROOT = db.ROOT
COWORK_APP = os.environ.get("COWORK_APP", "Claude")


CODE_KEYWORDS = {
    "clonar", "clone", "git ", "github", "repo", "repositório",
    "instalar", "install", "skill", "plugin", "pacote", "lib",
    "projeto em", "scaffold", "mvp", "implementar", "integrar",
    "config", "settings.json", "claude code", "cli", "stack",
    ".plist", "mcp", "n8n", "fastapi", "flask", "node", "python",
    "c#", "angular", "django", "react", "next", "build", "deploy",
    "compilar", "executar script", "subir container", "docker",
}

DESKTOP_KEYWORDS = {
    "ler ", "skim", "skimmar", "olhar", "ver vídeo", "ver video",
    "assistir", "navegar", "browse", "demo", "landing",
    "meta ads", "ads manager", "tiktok", "instagram", "youtube",
    "feed", "broadcast", "playbook", "thread", "artigo", "curso",
    "transcrever", "anotar", "notion", "obsidian", "registrar",
}

CODE_CATEGORIES = {
    "Claude Code", "Agents", "Scraping", "Automação", "Open-source",
    "AI Tools",
}

DESKTOP_CATEGORIES = {
    "Marketing", "Meta Ads", "TikTok", "SaaS", "Produtividade", "Meta",
}


def heuristic_tipo(op: dict) -> str:
    bag = " ".join(filter(None, [
        (op.get("acao_sugerida") or "").lower(),
        (op.get("insight") or "").lower(),
        (op.get("texto") or "").lower(),
    ]))
    code_hits    = sum(1 for kw in CODE_KEYWORDS    if kw in bag)
    desktop_hits = sum(1 for kw in DESKTOP_KEYWORDS if kw in bag)

    cat = op.get("categoria") or ""
    if cat in CODE_CATEGORIES:
        code_hits += 2
    if cat in DESKTOP_CATEGORIES:
        desktop_hits += 2

    if code_hits == 0 and desktop_hits == 0:
        return "claude"
    return "claude" if code_hits >= desktop_hits else "cowork"


def slugify(*parts: str) -> str:
    raw = " ".join(p for p in parts if p)
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    raw = raw.lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = raw.strip("-")
    return raw[:60] or "projeto"


def gerar_slug_para(op: dict) -> str:
    handle = (op.get("handle") or "").lstrip("@")
    keyword = (op.get("categoria") or op.get("autor") or "")
    insight = (op.get("insight") or op.get("acao_sugerida") or "")
    base = slugify(handle, keyword, insight.split(".")[0])
    candidate = base
    n = 2
    while db.get_projeto_by_slug(candidate):
        candidate = f"{base}-{n}"
        n += 1
    return candidate


PROMPT_I18N: dict[str, dict[str, str]] = {
    "en": {
        "header": (
            "Context: bookmark saved on X.\n"
            "Author: {autor} ({handle})\n"
            "Link: {link}\n"
            "Category: {categoria} · Priority: {prioridade}\n"
        ),
        "body": (
            "\nOriginal text:\n  {texto}\n"
            "\nTriage insight:\n  {insight}\n"
            "\nSuggested action:\n  {acao_sugerida}\n"
        ),
        "no_text": "(no text)",
        "claude": (
            "\n---\nYou're running inside `{projeto_path}` "
            "(a new folder created for this opportunity). Do the following:\n"
            "  1. Confirm you understood the opportunity.\n"
            "  2. Propose a 3-5 step plan to execute the suggested action.\n"
            "  3. After my OK, start implementing (create files, install deps, etc.).\n"
            "  4. When done, update the project's README.md with what was done.\n"
        ),
        "cowork": (
            "\n---\nThis opportunity needs desktop/visual interaction. "
            "Do the following:\n"
            "  1. Open the bookmark link in Chrome.\n"
            "  2. Execute the suggested action above (read, test, validate, take notes).\n"
            "  3. Come back with a summary of what you found (3-5 bullets).\n"
            "  4. Suggest the next step: archive / turn into project / dig deeper.\n"
        ),
    },
    "pt": {
        "header": (
            "Contexto: bookmark salvo no X.\n"
            "Autor: {autor} ({handle})\n"
            "Link: {link}\n"
            "Categoria: {categoria} · Prioridade: {prioridade}\n"
        ),
        "body": (
            "\nTexto original:\n  {texto}\n"
            "\nInsight da triagem:\n  {insight}\n"
            "\nAção sugerida:\n  {acao_sugerida}\n"
        ),
        "no_text": "(sem texto)",
        "claude": (
            "\n---\nVocê está rodando dentro de `{projeto_path}` "
            "(pasta nova criada para esta oportunidade). Faça o seguinte:\n"
            "  1. Confirme que entendeu a oportunidade.\n"
            "  2. Proponha um plano em 3-5 passos para executar a ação sugerida.\n"
            "  3. Após meu OK, comece a implementar (criar arquivos, instalar deps, etc.).\n"
            "  4. Quando terminar, atualize o README.md do projeto com o que foi feito.\n"
        ),
        "cowork": (
            "\n---\nEsta oportunidade exige interação visual/desktop. "
            "Faça o seguinte:\n"
            "  1. Abra o link do bookmark no Chrome.\n"
            "  2. Execute a ação sugerida acima (ler, testar, validar, anotar).\n"
            "  3. Volte com um resumo do que encontrou (3-5 bullets).\n"
            "  4. Sugira o próximo passo: arquivar / virar projeto / aprofundar.\n"
        ),
    },
    "es": {
        "header": (
            "Contexto: bookmark guardado en X.\n"
            "Autor: {autor} ({handle})\n"
            "Enlace: {link}\n"
            "Categoría: {categoria} · Prioridad: {prioridade}\n"
        ),
        "body": (
            "\nTexto original:\n  {texto}\n"
            "\nInsight de la triage:\n  {insight}\n"
            "\nAcción sugerida:\n  {acao_sugerida}\n"
        ),
        "no_text": "(sin texto)",
        "claude": (
            "\n---\nEstás corriendo dentro de `{projeto_path}` "
            "(carpeta nueva creada para esta oportunidad). Haz lo siguiente:\n"
            "  1. Confirma que entendiste la oportunidad.\n"
            "  2. Propón un plan de 3-5 pasos para ejecutar la acción sugerida.\n"
            "  3. Tras mi OK, comienza a implementar (crear archivos, instalar deps, etc.).\n"
            "  4. Cuando termines, actualiza el README.md del proyecto con lo hecho.\n"
        ),
        "cowork": (
            "\n---\nEsta oportunidad necesita interacción visual/desktop. "
            "Haz lo siguiente:\n"
            "  1. Abre el enlace del bookmark en Chrome.\n"
            "  2. Ejecuta la acción sugerida arriba (leer, probar, validar, anotar).\n"
            "  3. Vuelve con un resumen de lo que encontraste (3-5 bullets).\n"
            "  4. Sugiere el siguiente paso: archivar / convertir en proyecto / profundizar.\n"
        ),
    },
}


def _lang(lang: str | None) -> str:
    return lang if lang in PROMPT_I18N else "pt"


def montar_prompt(op: dict, *, tipo: str, projeto_path: Path | None = None,
                  lang: str = "pt") -> str:
    L = PROMPT_I18N[_lang(lang)]
    header = L["header"].format(
        autor=op.get("autor"), handle=op.get("handle"),
        link=op.get("link"), categoria=op.get("categoria"),
        prioridade=op.get("prioridade"),
    )
    body = L["body"].format(
        texto=op.get("texto") or L["no_text"],
        insight=op.get("insight"),
        acao_sugerida=op.get("acao_sugerida"),
    )
    outro = L["claude" if tipo == "claude" else "cowork"].format(projeto_path=projeto_path)
    return header + body + outro


def pbcopy(text: str) -> None:
    p = subprocess.run(["pbcopy"], input=text, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError("pbcopy failed (not on macOS?)")


def open_app(app_name: str) -> None:
    subprocess.run(["open", "-a", app_name], check=False)


def open_terminal_with_command(cwd: Path, cmd: str) -> None:
    full = f'cd {shlex.quote(str(cwd))} && {cmd}'
    apple = full.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "Terminal" to do script "{apple}"'
    subprocess.run(["osascript", "-e", script], check=False)
    subprocess.run(["osascript", "-e", 'tell application "Terminal" to activate'], check=False)


SCAFFOLD_I18N: dict[str, dict[str, str]] = {
    "en": {
        "readme": (
            "# {slug}\n\n"
            "Project bootstrapped from a bookmark saved on X.\n\n"
            "**Link**: {link}\n"
            "**Author**: {autor} ({handle})\n"
            "**Category**: {categoria} · **Priority**: {prioridade}\n"
            "**Bookmark date**: {data_bookmark}\n\n"
            "## Original text\n\n> {texto}\n\n"
            "## Triage insight\n\n{insight}\n\n"
            "## Suggested action\n\n{acao_sugerida}\n\n"
            "## Status\n\n- [ ] Plan defined\n- [ ] In progress\n- [ ] Done\n"
        ),
        "claude_md": (
            "# Context for Claude Code\n\n"
            "This project was spawned from an opportunity triaged in the bookmarks panel.\n\n"
            "## Goal\n\n{acao_sugerida}\n\n"
            "## Why it matters\n\n{insight}\n\n"
            "## Conventions\n\n"
            "- Save progress in `NOTES.md` at the end of each session.\n"
            "- Update the status checklist in `README.md`.\n"
            "- Small commits with descriptive messages.\n"
            "- When done, mark the opportunity as `executado` in the panel.\n"
        ),
        "no_text": "(no text)",
        "log_readme": "✓ README.md created",
        "log_claude": "✓ CLAUDE.md created",
        "commit_msg": "chore: initial scaffold from bookmarks panel",
    },
    "pt": {
        "readme": (
            "# {slug}\n\n"
            "Projeto criado a partir do bookmark salvo no X.\n\n"
            "**Link**: {link}\n"
            "**Autor**: {autor} ({handle})\n"
            "**Categoria**: {categoria} · **Prioridade**: {prioridade}\n"
            "**Data do bookmark**: {data_bookmark}\n\n"
            "## Texto original\n\n> {texto}\n\n"
            "## Insight da triagem\n\n{insight}\n\n"
            "## Ação sugerida\n\n{acao_sugerida}\n\n"
            "## Status\n\n- [ ] Plano definido\n- [ ] Em desenvolvimento\n- [ ] Concluído\n"
        ),
        "claude_md": (
            "# Contexto para o Claude Code\n\n"
            "Este projeto nasceu de uma oportunidade triada no painel de bookmarks.\n\n"
            "## Objetivo\n\n{acao_sugerida}\n\n"
            "## Por que importa\n\n{insight}\n\n"
            "## Convenções\n\n"
            "- Salvar progresso em `NOTES.md` ao final de cada sessão.\n"
            "- Atualizar o checklist de status no `README.md`.\n"
            "- Commits pequenos e mensagens descritivas.\n"
            "- Ao concluir, marque a oportunidade como `executado` no painel.\n"
        ),
        "no_text": "(sem texto)",
        "log_readme": "✓ README.md criado",
        "log_claude": "✓ CLAUDE.md criado",
        "commit_msg": "chore: scaffold inicial pelo painel de bookmarks",
    },
    "es": {
        "readme": (
            "# {slug}\n\n"
            "Proyecto creado a partir del bookmark guardado en X.\n\n"
            "**Enlace**: {link}\n"
            "**Autor**: {autor} ({handle})\n"
            "**Categoría**: {categoria} · **Prioridad**: {prioridade}\n"
            "**Fecha del bookmark**: {data_bookmark}\n\n"
            "## Texto original\n\n> {texto}\n\n"
            "## Insight de la triage\n\n{insight}\n\n"
            "## Acción sugerida\n\n{acao_sugerida}\n\n"
            "## Estado\n\n- [ ] Plan definido\n- [ ] En desarrollo\n- [ ] Concluido\n"
        ),
        "claude_md": (
            "# Contexto para Claude Code\n\n"
            "Este proyecto nació de una oportunidad triada en el panel de bookmarks.\n\n"
            "## Objetivo\n\n{acao_sugerida}\n\n"
            "## Por qué importa\n\n{insight}\n\n"
            "## Convenciones\n\n"
            "- Guardar progreso en `NOTES.md` al final de cada sesión.\n"
            "- Actualizar el checklist de estado en `README.md`.\n"
            "- Commits pequeños con mensajes descriptivos.\n"
            "- Al concluir, marca la oportunidad como `executado` en el panel.\n"
        ),
        "no_text": "(sin texto)",
        "log_readme": "✓ README.md creado",
        "log_claude": "✓ CLAUDE.md creado",
        "commit_msg": "chore: scaffold inicial desde el panel de bookmarks",
    },
}


def criar_projeto(op: dict, *, com_github: bool = False, lang: str = "pt") -> dict:
    L = SCAFFOLD_I18N[_lang(lang)]
    slug = gerar_slug_para(op)
    path = ROOT / slug
    path.mkdir(parents=True, exist_ok=True)

    log_lines: list[str] = []

    ctx = {
        "slug": slug,
        "link": op.get("link"),
        "autor": op.get("autor"),
        "handle": op.get("handle"),
        "categoria": op.get("categoria"),
        "prioridade": op.get("prioridade"),
        "data_bookmark": op.get("data_bookmark"),
        "texto": op.get("texto") or L["no_text"],
        "insight": op.get("insight"),
        "acao_sugerida": op.get("acao_sugerida"),
    }

    (path / "README.md").write_text(L["readme"].format(**ctx), encoding="utf-8")
    log_lines.append(L["log_readme"])

    (path / "CLAUDE.md").write_text(L["claude_md"].format(**ctx), encoding="utf-8")
    log_lines.append(L["log_claude"])

    if shutil.which("git"):
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=False)
        subprocess.run(["git", "add", "."], cwd=path, check=False)
        subprocess.run(
            ["git", "commit", "-q", "-m", L["commit_msg"]],
            cwd=path, check=False,
        )
        log_lines.append("✓ git init + commit inicial")
    else:
        log_lines.append("⚠ git não encontrado no PATH")

    github_url = None
    if com_github:
        if not shutil.which("gh"):
            log_lines.append("⚠ gh CLI não encontrado — pulei criação do repo no GitHub")
        else:
            try:
                desc = (op.get("insight") or "")[:120]
                p = subprocess.run(
                    ["gh", "repo", "create", slug, "--private",
                     "--source", str(path), "--push",
                     "--description", desc],
                    capture_output=True, text=True, check=False,
                )
                if p.returncode == 0:
                    out = (p.stdout or p.stderr).strip()
                    url_match = re.search(r"https?://github\.com/\S+", out)
                    github_url = url_match.group(0) if url_match else out.splitlines()[-1]
                    log_lines.append(f"✓ gh repo create → {github_url}")
                else:
                    log_lines.append(f"⚠ gh falhou: {p.stderr.strip()[:200]}")
            except Exception as e:
                log_lines.append(f"⚠ erro ao chamar gh: {e}")

    proj_id = db.insert_projeto(
        oportunidade_id=op["id"],
        nome=slug.replace("-", " ").title(),
        slug=slug,
        path=str(path),
        github_url=github_url,
    )

    db.update_oportunidade(op["id"], projeto_iniciado=1)

    return {
        "projeto_id": proj_id,
        "slug": slug,
        "path": str(path),
        "github_url": github_url,
        "log": "\n".join(log_lines),
    }


def executar(op_id: int, *, tipo_override: str | None = None,
             criar_projeto_flag: bool = False, com_github: bool = False,
             lang: str = "pt") -> dict:
    op = db.get_oportunidade(op_id)
    if not op:
        raise ValueError(f"Oportunidade #{op_id} não existe")

    tipo = tipo_override or op.get("tipo_execucao") or heuristic_tipo(op)
    if tipo not in ("claude", "cowork"):
        raise ValueError(f"Tipo inválido: {tipo}")

    log_lines: list[str] = [f"Tipo decidido: {tipo} (override={tipo_override}, lang={lang})"]
    projeto = None
    projeto_path = None

    if criar_projeto_flag:
        projeto = criar_projeto(op, com_github=com_github, lang=lang)
        projeto_path = Path(projeto["path"])
        log_lines.append(projeto["log"])

    prompt = montar_prompt(op, tipo=tipo, projeto_path=projeto_path, lang=lang)

    exec_id = db.log_execucao(
        op_id, tipo=tipo, prompt=prompt,
        projeto_path=str(projeto_path) if projeto_path else None,
    )

    try:
        if tipo == "claude":
            if projeto_path is None:
                projeto_path = ROOT
            try:
                pbcopy(prompt)
                log_lines.append("✓ prompt copiado pro clipboard")
            except Exception as e:
                log_lines.append(f"⚠ pbcopy falhou: {e}")
            cmd = "claude " + shlex.quote(prompt)
            open_terminal_with_command(projeto_path, cmd)
            log_lines.append(f"✓ Terminal aberto em {projeto_path}")
        else:
            try:
                pbcopy(prompt)
                log_lines.append("✓ prompt copiado pro clipboard")
            except Exception as e:
                log_lines.append(f"⚠ pbcopy falhou: {e}")
            open_app(COWORK_APP)
            log_lines.append(f"✓ Cowork ({COWORK_APP}) aberto — cole o prompt com ⌘V")

        db.finalize_execucao(exec_id, "concluida", "\n".join(log_lines))
        db.update_oportunidade(op_id, status="em_progresso", tipo_execucao=tipo)
        return {
            "ok": True,
            "exec_id": exec_id,
            "tipo": tipo,
            "projeto": projeto,
            "log": "\n".join(log_lines),
        }
    except Exception as e:
        log_lines.append(f"✖ erro: {e}")
        db.finalize_execucao(exec_id, "erro", "\n".join(log_lines))
        return {
            "ok": False,
            "exec_id": exec_id,
            "tipo": tipo,
            "projeto": projeto,
            "log": "\n".join(log_lines),
            "error": str(e),
        }
