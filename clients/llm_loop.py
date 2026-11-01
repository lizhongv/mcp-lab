"""LLM + MCP 工具调用循环。

需要环境变量：
  OPENAI_API_KEY   对话模型 Key
  OPENAI_BASE_URL  可选的 OpenAI 兼容地址
  OPENAI_MODEL     模型名，默认 deepseek-chat

用法：
  uv run python clients/llm_loop.py --server kb
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from openai import OpenAI

from clients.cli import server_params

MAX_ROUNDS = 6


def openai_tools(tools) -> list[dict]:  # noqa: ANN001
    """把 MCP 工具描述转成 OpenAI function calling 的格式。"""
    return [
        {
            "type": "function",
            "function": {
                "name": item.name,
                "description": item.description or "",
                "parameters": item.inputSchema,
            },
        }
        for item in tools
    ]


async def run(server: str, question: str) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("请先设置 OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    async with stdio_client(server_params(server)) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = openai_tools((await session.list_tools()).tools)
        messages = [{"role": "user", "content": question}]

        for _ in range(MAX_ROUNDS):
            response = client.chat.completions.create(model=model, messages=messages, tools=tools)
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                print(message.content or "")
                return
            for call in message.tool_calls:
                print(f"[调用工具] {call.function.name} {call.function.arguments}")
                result = await session.call_tool(call.function.name, json.loads(call.function.arguments))
                text = "\n".join(getattr(block, "text", str(block)) for block in result.content)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": text})

        print("达到最大轮数，仍未得到最终回答")


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM + MCP 工具循环")
    parser.add_argument("--server", choices=["kb", "files", "fetch"], default="kb")
    parser.add_argument("question", nargs="?", default="知识库里有哪些关于 MCP 的内容？")
    options = parser.parse_args()
    asyncio.run(run(options.server, options.question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
