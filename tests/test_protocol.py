"""协议级测试：真正启动 MCP 服务器，走 initialize / list_tools / call_tool。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def test_kb_server_over_stdio(tmp_path: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "servers.kb.server"],
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT),
            "MCP_KB_DB": str(tmp_path / "kb.sqlite"),
            "MCP_KB_SAMPLES": str(ROOT / "data" / "samples"),
        },
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = {tool.name for tool in (await session.list_tools()).tools}
        assert {"search", "get_document", "list_documents"} <= tools

        result = await session.call_tool("search", {"query": "MCP"})
        assert result.content
        text = "".join(getattr(block, "text", "") for block in result.content)
        assert "MCP" in text
