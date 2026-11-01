"""最小 MCP 客户端：列出工具或调用一次工具。

用法：
  uv run python -m clients.cli --server kb
  uv run python -m clients.cli --server kb --tool search --args '{"query":"MCP"}'
  uv run python -m clients.cli --server files --tool list_files --args '{"path":"."}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

# Windows 控制台默认 GBK，中文工具输出会乱码；统一切到 UTF-8。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SERVERS = {
    "kb": "servers.kb.server",
    "files": "servers.files.server",
    "fetch": "servers.fetch.server",
}


def server_params(name: str) -> StdioServerParameters:
    """用当前解释器启动服务器，并把项目根目录放进 PYTHONPATH。"""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", SERVERS[name]],
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )


async def run(server: str, tool: str | None, args: dict) -> None:
    async with stdio_client(server_params(server)) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        if tool is None:
            for item in tools.tools:
                print(f"- {item.name}: {item.description}")
            return
        result = await session.call_tool(tool, args)
        for block in result.content:
            text = getattr(block, "text", None)
            print(text if text is not None else block)


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP 最小客户端")
    parser.add_argument("--server", choices=sorted(SERVERS), default="kb")
    parser.add_argument("--tool", help="工具名；不填则列出所有工具")
    parser.add_argument("--args", default="{}", help="JSON 参数")
    options = parser.parse_args()
    try:
        args = json.loads(options.args)
    except json.JSONDecodeError as error:
        print(f"--args 不是合法 JSON：{error}", file=sys.stderr)
        return 2
    asyncio.run(run(options.server, options.tool, args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
