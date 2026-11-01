"""知识库 MCP 服务器：把 kb/core.py 暴露成工具。

启动：uv run python -m servers.kb.server
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from servers.kb import core
from shared.errors import ToolError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "kb.sqlite"
DEFAULT_SAMPLES = ROOT / "data" / "samples"

mcp = FastMCP("kb")


def _db_path() -> Path:
    return Path(os.getenv("MCP_KB_DB", str(DEFAULT_DB))).resolve()


@contextmanager
def _conn():
    conn = core.connect(_db_path())
    core.seed_if_empty(conn, Path(os.getenv("MCP_KB_SAMPLES", str(DEFAULT_SAMPLES))))
    try:
        yield conn
    finally:
        conn.close()


@mcp.tool()
def search(query: str, limit: int = 5) -> list[dict]:
    """按关键词检索知识库，返回编号、标题、摘要与相关度分数。

    Args:
        query: 检索词，至少 3 个字符时使用全文索引。
        limit: 返回条数，1～20。
    """
    try:
        with _conn() as conn:
            return core.search_documents(conn, query, limit)
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


@mcp.tool()
def get_document(doc_id: int) -> dict:
    """按编号读取一篇文档的完整正文。"""
    try:
        with _conn() as conn:
            return core.get_document(conn, doc_id)
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


@mcp.tool()
def list_documents(limit: int = 20, offset: int = 0) -> list[dict]:
    """列出知识库中的文档，用于发现有哪些内容可读。"""
    with _conn() as conn:
        return core.list_documents(conn, limit, offset)


if __name__ == "__main__":
    logging.getLogger("mcp").setLevel(logging.WARNING)
    mcp.run(transport="stdio")
