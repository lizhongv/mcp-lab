"""文件沙箱核心：所有操作都经 safe_path 校验。"""

from __future__ import annotations

from pathlib import Path

from shared.errors import ToolError
from shared.paths import safe_path


def _entry(path: Path, root: Path) -> dict:
    stat = path.stat()
    return {
        "path": path.relative_to(root).as_posix(),
        "type": "dir" if path.is_dir() else "file",
        "bytes": stat.st_size,
        "mtime": int(stat.st_mtime),
    }


def list_dir(root: Path, relative: str = ".") -> list[dict]:
    target = safe_path(root, relative)
    if not target.is_dir():
        raise ToolError("NOT_A_DIRECTORY", f"不是目录：{relative}")
    return [_entry(item, root.resolve()) for item in sorted(target.iterdir())]


def stat_path(root: Path, relative: str) -> dict:
    target = safe_path(root, relative)
    if not target.exists():
        raise ToolError("NOT_FOUND", f"路径不存在：{relative}")
    return _entry(target, root.resolve())


def read_text(root: Path, relative: str, max_bytes: int = 65536) -> dict:
    target = safe_path(root, relative)
    if not target.is_file():
        raise ToolError("NOT_A_FILE", f"不是文件：{relative}")
    max_bytes = max(1, min(max_bytes, 1024 * 1024))
    data = target.read_bytes()[:max_bytes]
    if b"\x00" in data:
        raise ToolError("BINARY_FILE", "这是二进制文件，read_text 只读文本")
    return {
        "path": target.relative_to(root.resolve()).as_posix(),
        "content": data.decode("utf-8", "replace"),
        "truncated": target.stat().st_size > max_bytes,
    }


def write_text(root: Path, relative: str, content: str, allow_write: bool) -> dict:
    if not allow_write:
        raise ToolError("WRITE_DISABLED", "写入被禁用；设置 MCP_FILES_ALLOW_WRITE=1 后重试")
    target = safe_path(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"path": target.relative_to(root.resolve()).as_posix(), "bytes": len(content.encode("utf-8"))}
