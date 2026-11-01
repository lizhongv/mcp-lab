"""路径沙箱：所有文件类工具都必须经过这里。

规则：
  1. 只接受相对路径，拒绝绝对路径与盘符；
  2. 拼接后 resolve()，结果必须仍在根目录内；
  3. resolve() 会展开符号链接，因此链接指向根目录外也会被拒绝。
MCP 服务器被模型调用，模型可能被提示词注入诱导去读 /etc/passwd 或 ../ 之外的
文件；路径校验必须放在服务端，不能指望客户端。
"""

from __future__ import annotations

from pathlib import Path

from .errors import ToolError


def ensure_dir(path: Path) -> Path:
    """确保目录存在并返回 resolve 后的路径。"""
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def safe_path(root: Path, user_path: str) -> Path:
    """把用户给的相对路径解析为根目录内的绝对路径；越界抛 ToolError。"""
    if not user_path or "\x00" in user_path:
        raise ToolError("INVALID_PATH", "路径不能为空，也不能包含空字节")

    raw = Path(user_path)
    if raw.is_absolute() or raw.drive:
        raise ToolError("INVALID_PATH", f"只接受相对路径：{user_path}")

    root = root.resolve()
    candidate = (root / raw).resolve()
    if candidate != root and root not in candidate.parents:
        raise ToolError("PATH_ESCAPE", f"路径越出根目录：{user_path}")
    return candidate
