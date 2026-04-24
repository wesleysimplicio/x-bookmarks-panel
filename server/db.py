"""
SQLite layer for the bookmarks panel.

Tables:
- oportunidades: each triaged bookmark (1:1 with an x.com link)
- execucoes:     log of every "Execute" button click (Claude or Cowork)
- projetos:      scaffold folders created under <root>/<slug>/
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "bookmarks.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS oportunidades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    link            TEXT UNIQUE NOT NULL,
    autor           TEXT,
    handle          TEXT,
    texto           TEXT,
    data_bookmark   TEXT,
    midia           TEXT,
    categoria       TEXT,
    prioridade      TEXT CHECK (prioridade IN ('agir-agora','estudar-depois','arquivar')),
    insight         TEXT,
    acao_sugerida   TEXT,
    vale_executar   INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'novo'
                    CHECK (status IN ('novo','em_progresso','executado','arquivado','descartado')),
    tipo_execucao   TEXT,
    notas           TEXT,
    instalado          INTEGER DEFAULT 0,
    aplicado           INTEGER DEFAULT 0,
    projeto_iniciado   INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_op_status     ON oportunidades(status);
CREATE INDEX IF NOT EXISTS idx_op_prioridade ON oportunidades(prioridade);
CREATE INDEX IF NOT EXISTS idx_op_categoria  ON oportunidades(categoria);

CREATE TABLE IF NOT EXISTS execucoes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    oportunidade_id  INTEGER NOT NULL,
    tipo             TEXT NOT NULL,
    prompt           TEXT,
    projeto_path     TEXT,
    status           TEXT DEFAULT 'iniciada'
                     CHECK (status IN ('iniciada','concluida','erro')),
    log              TEXT,
    started_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at      TEXT,
    FOREIGN KEY (oportunidade_id) REFERENCES oportunidades(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ex_op ON execucoes(oportunidade_id);

CREATE TABLE IF NOT EXISTS projetos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    oportunidade_id  INTEGER,
    nome             TEXT,
    slug             TEXT UNIQUE NOT NULL,
    path             TEXT NOT NULL,
    github_url       TEXT,
    status           TEXT DEFAULT 'criado'
                     CHECK (status IN ('criado','ativo','pausado','arquivado')),
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (oportunidade_id) REFERENCES oportunidades(id) ON DELETE SET NULL
);

CREATE TRIGGER IF NOT EXISTS oportunidades_updated_at
AFTER UPDATE ON oportunidades
FOR EACH ROW
BEGIN
    UPDATE oportunidades SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
"""


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    migrate()


def migrate() -> None:
    with connect() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(oportunidades)").fetchall()}
        for col in ("instalado", "aplicado", "projeto_iniciado"):
            if col not in cols:
                conn.execute(
                    f"ALTER TABLE oportunidades ADD COLUMN {col} INTEGER DEFAULT 0"
                )
        conn.commit()


@contextmanager
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def upsert_oportunidade(row: dict) -> tuple[int, bool]:
    with connect() as conn:
        cur = conn.execute("SELECT id FROM oportunidades WHERE link = ?", (row["link"],))
        existing = cur.fetchone()
        if existing:
            conn.execute(
                """UPDATE oportunidades SET
                       autor=?, handle=?, texto=?, data_bookmark=?, midia=?,
                       categoria=?, prioridade=?, insight=?, acao_sugerida=?, vale_executar=?
                   WHERE id=?""",
                (
                    row.get("autor"), row.get("handle"), row.get("texto"),
                    row.get("data_bookmark"), row.get("midia"),
                    row.get("categoria"), row.get("prioridade"),
                    row.get("insight"), row.get("acao_sugerida"),
                    int(bool(row.get("vale_executar"))),
                    existing["id"],
                ),
            )
            conn.commit()
            return existing["id"], False
        cur = conn.execute(
            """INSERT INTO oportunidades
               (link, autor, handle, texto, data_bookmark, midia, categoria,
                prioridade, insight, acao_sugerida, vale_executar)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["link"], row.get("autor"), row.get("handle"), row.get("texto"),
                row.get("data_bookmark"), row.get("midia"), row.get("categoria"),
                row.get("prioridade"), row.get("insight"), row.get("acao_sugerida"),
                int(bool(row.get("vale_executar"))),
            ),
        )
        conn.commit()
        return cur.lastrowid, True


def list_oportunidades(
    *, status: Optional[str] = None,
    prioridade: Optional[str] = None,
    categoria: Optional[str] = None,
) -> list[dict]:
    sql = "SELECT * FROM oportunidades WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if prioridade:
        sql += " AND prioridade = ?"
        params.append(prioridade)
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    sql += """ ORDER BY
        CASE prioridade
            WHEN 'agir-agora' THEN 0
            WHEN 'estudar-depois' THEN 1
            WHEN 'arquivar' THEN 2
            ELSE 99
        END,
        CASE status
            WHEN 'novo' THEN 0
            WHEN 'em_progresso' THEN 1
            WHEN 'executado' THEN 2
            WHEN 'arquivado' THEN 3
            WHEN 'descartado' THEN 4
        END,
        data_bookmark DESC"""
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_oportunidade(op_id: int) -> Optional[dict]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM oportunidades WHERE id = ?", (op_id,)).fetchone()
        return dict(r) if r else None


def update_oportunidade(op_id: int, **fields) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [op_id]
    with connect() as conn:
        conn.execute(f"UPDATE oportunidades SET {cols} WHERE id = ?", params)
        conn.commit()


def log_execucao(
    op_id: int, tipo: str, prompt: str | None = None,
    projeto_path: str | None = None,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO execucoes (oportunidade_id, tipo, prompt, projeto_path)
               VALUES (?,?,?,?)""",
            (op_id, tipo, prompt, projeto_path),
        )
        conn.commit()
        return cur.lastrowid


def finalize_execucao(exec_id: int, status: str, log: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            """UPDATE execucoes
               SET status=?, log=?, finished_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (status, log, exec_id),
        )
        conn.commit()


def list_execucoes(op_id: int | None = None) -> list[dict]:
    with connect() as conn:
        if op_id is not None:
            sql = "SELECT * FROM execucoes WHERE oportunidade_id = ? ORDER BY id DESC"
            return [dict(r) for r in conn.execute(sql, (op_id,)).fetchall()]
        sql = "SELECT * FROM execucoes ORDER BY id DESC LIMIT 100"
        return [dict(r) for r in conn.execute(sql).fetchall()]


def insert_projeto(
    *, oportunidade_id: int | None, nome: str, slug: str, path: str,
    github_url: str | None = None,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO projetos (oportunidade_id, nome, slug, path, github_url)
               VALUES (?,?,?,?,?)""",
            (oportunidade_id, nome, slug, path, github_url),
        )
        conn.commit()
        return cur.lastrowid


def list_projetos() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT p.*, o.handle, o.insight FROM projetos p
               LEFT JOIN oportunidades o ON o.id = p.oportunidade_id
               ORDER BY p.created_at DESC""").fetchall()]


def update_projeto(proj_id: int, **fields) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [proj_id]
    with connect() as conn:
        conn.execute(f"UPDATE projetos SET {cols} WHERE id = ?", params)
        conn.commit()


def get_projeto_by_slug(slug: str) -> Optional[dict]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM projetos WHERE slug = ?", (slug,)).fetchone()
        return dict(r) if r else None


def stats() -> dict:
    with connect() as conn:
        def one(sql: str, *p) -> int:
            return conn.execute(sql, p).fetchone()[0]
        return {
            "total":          one("SELECT COUNT(*) FROM oportunidades"),
            "agir_agora":     one("SELECT COUNT(*) FROM oportunidades WHERE prioridade='agir-agora'"),
            "estudar":        one("SELECT COUNT(*) FROM oportunidades WHERE prioridade='estudar-depois'"),
            "arquivar":       one("SELECT COUNT(*) FROM oportunidades WHERE prioridade='arquivar'"),
            "novo":           one("SELECT COUNT(*) FROM oportunidades WHERE status='novo'"),
            "em_progresso":   one("SELECT COUNT(*) FROM oportunidades WHERE status='em_progresso'"),
            "executado":      one("SELECT COUNT(*) FROM oportunidades WHERE status='executado'"),
            "vale_executar":  one("SELECT COUNT(*) FROM oportunidades WHERE vale_executar=1"),
            "projetos":       one("SELECT COUNT(*) FROM projetos"),
            "execucoes":      one("SELECT COUNT(*) FROM execucoes"),
        }


if __name__ == "__main__":
    init_db()
    print(f"DB inicializado em {DB_PATH}")
