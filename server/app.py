"""
Bookmarks panel — Flask server.

Runs on http://127.0.0.1:8765 (configurable via BOOKMARKS_PORT env var).

Routes:
- GET  /                                 -> index.html
- GET  /relatorio                        -> HTML report (if present)
- GET  /api/healthz                      -> ping
- GET  /api/stats                        -> counters
- GET  /api/oportunidades                -> list (filters: status, prioridade, categoria)
- GET  /api/oportunidades/<id>           -> detail + executions
- POST /api/oportunidades/<id>           -> update editable fields
- POST /api/oportunidades/<id>/executar  -> dispatch Claude / Cowork
- POST /api/oportunidades/import         -> re-import from HTML
- GET  /api/projetos                     -> list scaffolded projects
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

import db
import executor
import importer

PORT = int(os.environ.get("BOOKMARKS_PORT", "8765"))
HOST = os.environ.get("BOOKMARKS_HOST", "127.0.0.1")
ROOT = db.ROOT

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/relatorio")
def relatorio():
    return send_from_directory(ROOT, "relatorio-bookmarks-x.html")


@app.route("/api/healthz")
def healthz():
    return {"ok": True, "port": PORT}


@app.route("/api/stats")
def api_stats():
    return jsonify(db.stats())


@app.route("/api/oportunidades")
def api_list():
    return jsonify(db.list_oportunidades(
        status=request.args.get("status") or None,
        prioridade=request.args.get("prioridade") or None,
        categoria=request.args.get("categoria") or None,
    ))


@app.route("/api/oportunidades/<int:op_id>")
def api_get(op_id: int):
    op = db.get_oportunidade(op_id)
    if not op:
        return {"error": "not found"}, 404
    op["execucoes"] = db.list_execucoes(op_id)
    return jsonify(op)


@app.route("/api/oportunidades/<int:op_id>", methods=["POST"])
def api_update(op_id: int):
    body = request.get_json(silent=True) or {}
    allowed = {
        "status", "tipo_execucao", "notas", "prioridade",
        "instalado", "aplicado", "projeto_iniciado",
    }
    bool_cols = {"instalado", "aplicado", "projeto_iniciado"}
    fields = {}
    for k, v in body.items():
        if k not in allowed:
            continue
        fields[k] = int(bool(v)) if k in bool_cols else v
    if not fields:
        return {"error": "nothing to update"}, 400
    db.update_oportunidade(op_id, **fields)
    return jsonify(db.get_oportunidade(op_id))


@app.route("/api/oportunidades/<int:op_id>/executar", methods=["POST"])
def api_executar(op_id: int):
    body = request.get_json(silent=True) or {}
    tipo = body.get("tipo")
    if tipo not in (None, "claude", "cowork", "auto"):
        return {"error": "tipo inválido"}, 400
    if tipo == "auto":
        tipo = None
    criar = bool(body.get("criar_projeto"))
    com_github = bool(body.get("com_github"))
    lang = body.get("lang") if body.get("lang") in ("en", "pt", "es") else "pt"
    try:
        result = executor.executar(
            op_id,
            tipo_override=tipo,
            criar_projeto_flag=criar,
            com_github=com_github,
            lang=lang,
        )
    except Exception as e:
        return {"error": str(e)}, 500
    return jsonify(result)


@app.route("/api/oportunidades/import", methods=["POST"])
def api_import():
    try:
        result = importer.import_html()
    except Exception as e:
        return {"error": str(e)}, 500
    return jsonify(result)


@app.route("/api/projetos")
def api_projetos():
    return jsonify(db.list_projetos())


def main():
    db.init_db()
    try:
        res = importer.import_html()
        print(f"[importer] {res}")
    except FileNotFoundError as e:
        print(f"[importer] skip: {e}")
    print(f"Panel listening on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
