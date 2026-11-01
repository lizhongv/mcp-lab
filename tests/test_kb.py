"""知识库核心测试：不启动 MCP，直接测业务逻辑。"""

from __future__ import annotations

from pathlib import Path

import pytest

from servers.kb import core
from shared.errors import ToolError

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_seed_search_and_read(tmp_path: Path) -> None:
    conn = core.connect(tmp_path / "kb.sqlite")
    assert core.seed_if_empty(conn, SAMPLES) == 3

    hits = core.search_documents(conn, "MCP")
    assert hits and any("MCP" in hit["title"] for hit in hits)
    doc = core.get_document(conn, hits[0]["id"])
    assert doc["body"]

    listed = core.list_documents(conn)
    assert len(listed) == 3


def test_short_chinese_query_falls_back_to_like(tmp_path: Path) -> None:
    conn = core.connect(tmp_path / "kb.sqlite")
    core.seed_if_empty(conn, SAMPLES)
    hits = core.search_documents(conn, "工具")
    assert hits


def test_empty_query_is_rejected(tmp_path: Path) -> None:
    conn = core.connect(tmp_path / "kb.sqlite")
    with pytest.raises(ToolError):
        core.search_documents(conn, "   ")


def test_missing_document(tmp_path: Path) -> None:
    conn = core.connect(tmp_path / "kb.sqlite")
    with pytest.raises(ToolError):
        core.get_document(conn, 9999)
