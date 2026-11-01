# 05 · 测试与接入

## 两层测试

1. **核心层**：直接调用 `core.py`，覆盖业务逻辑与边界（路径穿越、写入开关、SSRF、短查询回退）。快、稳定。
2. **协议层**：真正启动 stdio 服务器，走 `initialize → list_tools → call_tool`。验证工具是否注册成功、参数 schema 是否能被调用、结果是否能序列化。

`tests/test_protocol.py` 是最小示例：

```python
params = StdioServerParameters(
    command=sys.executable,
    args=["servers/kb/server.py"],
    env={**os.environ, "PYTHONPATH": str(ROOT), "MCP_KB_DB": str(tmp_path / "kb.sqlite")},
)
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        await session.call_tool("search", {"query": "MCP"})
```

## 手工验证

```bash
npx -y @modelcontextprotocol/inspector uv run python -m servers.kb.server
```

Inspector 可以看工具列表、参数 schema、每次调用的请求与响应，是排查「模型为什么没调对」的第一站。

## 接入 Claude Code

在项目或用户配置里加一个 MCP 服务器（路径按你的实际位置）：

```json
{
  "mcpServers": {
    "mcp-lab-kb": {
      "command": "uv",
      "args": ["run", "python", "servers/kb/server.py"],
      "cwd": "D:/Users/zhongli2/Documents/code/mcp-lab"
    }
  }
}
```

## 接入知源

知源的检索接口是 `KnowledgeBase.search`。有两种接法：

1. **HTTP 桥**：把 MCP 服务器再包一层 FastAPI，知源通过 HTTP 调用；
2. **直接复用 core**：在知源里 import 本仓库的 `servers/kb/core.py`，把检索结果转成 `Hit`。

前者解耦，后者少一跳。无论哪种，都建议先保留原来的向量检索，用评测对比「加图谱/加 FTS」是否真的提升，再决定是否上线。

## 提交前检查

- [ ] `uv run pytest -q` 全绿
- [ ] `uv run ruff check .` 无告警
- [ ] 新增工具在描述里写清参数边界
- [ ] 新增文件/网络/命令能力有对应的安全测试
- [ ] 没有把 Key、真实数据、日志提交进仓库
