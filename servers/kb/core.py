"""知识库核心：SQLite FTS5 检索。

与 MCP 无关的业务逻辑放在这里，server.py 只负责把它暴露成工具。
这样核心逻辑可以用普通单元测试覆盖，不必每次都启动 MCP 协议。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shared.errors import ToolError

SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
    title,
    body,
    tokenize = 'trigram'
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """打开数据库并确保表存在。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError:
        # 老版本 SQLite 没有 trigram 分词器，退回默认分词；中文检索会退化。
        conn.executescript(SCHEMA.replace(", tokenize = 'trigram'", ""))
    return conn


def _title_of(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def seed_if_empty(conn: sqlite3.Connection, samples_dir: Path) -> int:
    """空库时导入 samples_dir 下的 Markdown，返回导入条数。"""
    count = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    if count:
        return 0
    inserted = 0
    for path in sorted(samples_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        conn.execute("INSERT INTO docs (title, body) VALUES (?, ?)", (_title_of(path, text), text))
        inserted += 1
    conn.commit()
    return inserted


def _like_snippet(body: str, query: str, radius: int = 60) -> str:
    index = body.lower().find(query.lower())
    if index < 0:
        return body[: radius * 2].replace("\n", " ")
    start = max(0, index - radius)
    end = min(len(body), index + len(query) + radius)
    return ("…" if start else "") + body[start:end].replace("\n", " ") + ("…" if end < len(body) else "")


def search_documents(conn: sqlite3.Connection, query: str, limit: int = 5) -> list[dict]:
    """按相关度检索；短查询或 FTS 不可用时退回 LIKE。"""
    query = query.strip()
    if not query:
        raise ToolError("INVALID_ARGUMENT", "query 不能为空")
    limit = max(1, min(limit, 20))

    try:
        if len(query) < 3:
            raise sqlite3.OperationalError("trigram 至少需要 3 个字符")
        phrase = '"' + query.replace('"', '""') + '"'
        rows = conn.execute(
            """
            SELECT rowid AS id, title, snippet(docs, 1, '[', ']', '…', 12) AS snippet,
                   bm25(docs) AS score
            FROM docs WHERE docs MATCH ? ORDER BY score LIMIT ?
            """,
            (phrase, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            "SELECT rowid AS id, title, body FROM docs WHERE title LIKE ? OR body LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [
            {"id": row["id"], "title": row["title"], "snippet": _like_snippet(row["body"], query), "score": None}
            for row in rows
        ]

    return [
        {"id": row["id"], "title": row["title"], "snippet": row["snippet"], "score": row["score"]}
        for row in rows
    ]


def get_document(conn: sqlite3.Connection, doc_id: int) -> dict:
    row = conn.execute("SELECT rowid AS id, title, body FROM docs WHERE rowid = ?", (doc_id,)).fetchone()
    if row is None:
        raise ToolError("NOT_FOUND", f"没有编号为 {doc_id} 的文档")
    return {"id": row["id"], "title": row["title"], "body": row["body"]}


def list_documents(conn: sqlite3.Connection, limit: int = 20, offset: int = 0) -> list[dict]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    rows = conn.execute(
        "SELECT rowid AS id, title, length(body) AS chars FROM docs ORDER BY rowid LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [{"id": row["id"], "title": row["title"], "chars": row["chars"]} for row in rows]
