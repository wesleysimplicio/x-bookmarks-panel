"""
Importer: reads the `BOOKMARKS` array from the HTML report and populates SQLite.

Expected HTML shape — see `examples/sample-relatorio.html`:

    const BOOKMARKS = [
      {
        "link": "https://x.com/example/status/1",
        "autor": "Display Name",
        "handle": "@example",
        "texto": "tweet body",
        "data": "YYYY-MM-DD",
        "midia": "texto|imagem|video|link",
        "categoria": "AI Tools|Marketing|...",
        "prioridade": "agir-agora|estudar-depois|arquivar",
        "insight": "porque importa",
        "acao_sugerida": "o que fazer",
        "vale_executar": true
      }
    ];

Idempotent: links already imported are updated, new ones inserted.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from db import ROOT, init_db, upsert_oportunidade

HTML_PATH = Path(os.environ.get("BOOKMARKS_HTML", ROOT / "relatorio-bookmarks-x.html"))


def extract_bookmarks_array(html: str) -> list[dict]:
    m = re.search(r"const\s+BOOKMARKS\s*=\s*(\[[\s\S]*?\n\]);", html)
    if not m:
        raise RuntimeError(
            "Could not find `const BOOKMARKS = [ ... ];` block in HTML. "
            "See examples/sample-relatorio.html for the expected format."
        )
    raw = m.group(1)
    raw_clean = re.sub(r",(\s*[}\]])", r"\1", raw)
    return json.loads(raw_clean)


def import_html(html_path: Path | None = None) -> dict:
    html_path = html_path or HTML_PATH
    if not html_path.exists():
        raise FileNotFoundError(f"HTML not found: {html_path}")
    html = html_path.read_text(encoding="utf-8")
    items = extract_bookmarks_array(html)

    inseridos, atualizados = 0, 0
    for it in items:
        row = {
            "link":           it.get("link"),
            "autor":          it.get("autor"),
            "handle":         it.get("handle"),
            "texto":          it.get("texto"),
            "data_bookmark":  it.get("data"),
            "midia":          it.get("midia"),
            "categoria":      it.get("categoria"),
            "prioridade":     it.get("prioridade"),
            "insight":        it.get("insight"),
            "acao_sugerida":  it.get("acao_sugerida"),
            "vale_executar":  bool(it.get("vale_executar")),
        }
        if not row["link"]:
            continue
        _, was_new = upsert_oportunidade(row)
        if was_new:
            inseridos += 1
        else:
            atualizados += 1

    return {"inseridos": inseridos, "atualizados": atualizados, "total": len(items)}


if __name__ == "__main__":
    init_db()
    res = import_html()
    print(f"Import done: {res}")
