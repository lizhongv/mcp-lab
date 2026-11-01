"""文件沙箱测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from servers.files import core
from shared.errors import ToolError


def test_read_and_list(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    entries = core.list_dir(tmp_path)
    assert {entry["path"] for entry in entries} == {"a.txt", "sub"}

    result = core.read_text(tmp_path, "a.txt")
    assert result["content"] == "hello" and not result["truncated"]


def test_read_truncates(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_text("x" * 100, encoding="utf-8")
    result = core.read_text(tmp_path, "big.txt", max_bytes=10)
    assert result["truncated"] and len(result["content"]) == 10


def test_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ToolError):
        core.read_text(tmp_path, "../secret.txt")


def test_write_is_disabled_by_default(tmp_path: Path) -> None:
    with pytest.raises(ToolError) as error:
        core.write_text(tmp_path, "a.txt", "hello", allow_write=False)
    assert error.value.code == "WRITE_DISABLED"


def test_write_inside_root(tmp_path: Path) -> None:
    result = core.write_text(tmp_path, "sub/a.txt", "hello", allow_write=True)
    assert result["bytes"] == 5
    assert (tmp_path / "sub" / "a.txt").read_text(encoding="utf-8") == "hello"


def test_binary_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"\x00\x01\x02")
    with pytest.raises(ToolError) as error:
        core.read_text(tmp_path, "a.bin")
    assert error.value.code == "BINARY_FILE"
