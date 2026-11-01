"""网页抓取 MCP 服务器。

启动：uv run python -m servers.fetch.server
环境变量：
  MCP_FETCH_ALLOW_PRIVATE 设为 1 时允许抓取内网地址（仅用于本地测试）
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from servers.fetch import core
from shared.errors import ToolError

mcp = FastMCP("fetch")


@mcp.tool()
async def fetch_url(url: str, max_chars: int = 8000) -> dict:
    """抓取一个公开网页，返回状态码、内容类型与转成纯文本后的正文。

    默认拒绝内网、回环与链路本地地址，也不自动跟随重定向。
    """
    try:
        return await core.fetch_url(url, max_chars, os.getenv("MCP_FETCH_ALLOW_PRIVATE") == "1")
    except ToolError as error:
        raise ValueError(f"{error.code}: {error.message}") from error


if __name__ == "__main__":
    logging.getLogger("mcp").setLevel(logging.WARNING)
    mcp.run(transport="stdio")
