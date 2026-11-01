"""文件沙箱 MCP 服务器。

启动：uv run python -m servers.files.server
环境变量：
  MCP_FILES_ROOT        沙箱根目录，默认 data/files
  MCP_FILES_ALLOW_WRITE 设为 1 才允许写文件，默认只读
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from servers.files import core
from shared.errors import ToolError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = ROOT / "data" / "files"

mcp = FastMCP("files")


def _root() -> Path:
    root = Path(os.getenv("MCP_FILES_ROOT", str(DEFAULT_ROOT))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _allow_write() -> bool:
    return os.getenv("MCP_FILES_ALLOW_WRITE", "0") == "1"


@mcp.tool()
def list_files(path: str = ".") -> list[dict]:
    """列出沙箱目录下的文件与子目录。path 必须是相对路径。"""
    try:
        return core.list_dir(_root(), path)
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


@mcp.tool()
def read_text(path: str, max_bytes: int = 65536) -> dict:
    """读取沙箱内的文本文件；超过 max_bytes 时截断并标记 truncated。"""
    try:
        return core.read_text(_root(), path, max_bytes)
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


@mcp.tool()
def write_text(path: str, content: str) -> dict:
    """写入文本文件；默认禁用，需要环境变量 MCP_FILES_ALLOW_WRITE=1。"""
    try:
        return core.write_text(_root(), path, content, _allow_write())
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


@mcp.tool()
def stat_path(path: str) -> dict:
    """查看沙箱内某个路径的类型、大小与修改时间。"""
    try:
        return core.stat_path(_root(), path)
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


if __name__ == "__main__":
    logging.getLogger("mcp").setLevel(logging.WARNING)
    mcp.run(transport="stdio")
