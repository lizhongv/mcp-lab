"""路径沙箱测试：越权路径必须被拒绝。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from shared.errors import ToolError
from shared.paths import safe_path


def test_relative_path_inside_root(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    assert safe_path(tmp_path, "sub/file.txt") == (tmp_path / "sub" / "file.txt").resolve()


def test_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ToolError) as error:
        safe_path(tmp_path, "../secret.txt")
    assert error.value.code == "PATH_ESCAPE"


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ToolError) as error:
        safe_path(tmp_path, str(tmp_path / "file.txt"))
    assert error.value.code == "INVALID_PATH"


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("当前系统不允许创建符号链接")
    with pytest.raises(ToolError) as error:
        safe_path(tmp_path, "link/file.txt")
    assert error.value.code == "PATH_ESCAPE"
