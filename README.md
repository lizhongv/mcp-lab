# MCP Lab · 从零构建可测试的 MCP 服务器

一个用来学 **MCP（Model Context Protocol）** 的最小实验室：三个有代表性的服务器、一个最小客户端、一套协议级测试，以及贯穿始终的安全边界。

> 定位：教学与自用，不是框架。每个服务器 100～200 行，读完能自己加第四个。

## 包含什么

| 服务器 | 工具 | 教什么 |
| --- | --- | --- |
| `servers/kb` | `search`、`get_document`、`list_documents` | 工具设计、SQLite FTS5 检索、分页与截断 |
| `servers/files` | `list_files`、`read_text`、`write_text`、`stat_path` | **路径沙箱**、只读优先、写操作显式开启 |
| `servers/fetch` | `fetch_url` | HTTP 抓取、**SSRF 防护**、内容类型与大小限制 |

客户端：

- `clients/cli.py`：列出工具、调用一次工具，用来验证服务器；
- `clients/llm_loop.py`：把 MCP 工具交给 OpenAI 兼容模型，走一遍工具调用循环（Key 只从环境变量读取）。

## 快速开始

```bash
uv sync

# 1. 列出知识库服务器的工具
uv run python -m clients.cli --server kb

# 2. 调用检索
uv run python -m clients.cli --server kb --tool search --args '{"query":"MCP"}'

# 3. 让模型自己决定调用哪个工具（需要 OPENAI_API_KEY）
export OPENAI_API_KEY=...
uv run python -m clients.llm_loop --server kb "知识库里有哪些关于 RAG 的内容？"
```

单独启动服务器（stdio）：

```bash
uv run python -m servers.kb.server
uv run python -m servers.files.server
uv run python -m servers.fetch.server
```

用官方 Inspector 手工调试：

```bash
npx -y @modelcontextprotocol/inspector uv run python -m servers.kb.server
```

## 版本说明

本仓库锁定 `mcp[cli]>=1.6,<2`：1.x 的 `FastMCP` API 与主流示例一致。MCP SDK 2.x 把 `FastMCP` 改名为 `MCPServer`，迁移步骤见官方迁移指南；升级时只需改各 `server.py` 的导入与实例化。

## 安全边界

这三个服务器刻意把「模型不可信」写进代码：

- **文件**：只接受相对路径；`resolve()` 后必须仍在根目录内；符号链接指向外面也会被拒绝；写入默认关闭，需要 `MCP_FILES_ALLOW_WRITE=1`。
- **抓取**：只允许 http/https；解析域名后拒绝回环、内网、链路本地、保留地址（SSRF）；不自动跟随重定向；限制 10 秒与 1 MB。
- **知识库**：只读；查询长度与返回条数有上限。
- **凭证**：任何 Key 只从环境变量读取，代码与文档里不写。

这些规则都在 `shared/` 与各 `core.py` 里，并有对应测试。

## 目录结构

```
mcp-lab/
├── servers/{kb,files,fetch}/   core.py（业务逻辑）+ server.py（MCP 绑定）
├── clients/                    cli.py、llm_loop.py
├── shared/                     路径沙箱、工具错误
├── tests/                      单元测试 + 协议级测试
├── docs/                       讲义
└── data/                       合成样例文档与沙箱目录
```

把业务逻辑放在 `core.py`、MCP 绑定放在 `server.py`，是为了让核心逻辑能用普通单元测试覆盖，协议层单独测。

## 测试

```bash
uv run pytest -q
uv run ruff check .
```

测试覆盖：路径穿越、符号链接逃逸、写入开关、二进制文件、短查询回退、HTML 转文本、SSRF 拦截，以及真实启动 stdio 服务器的 `initialize → list_tools → call_tool` 流程。

## 讲义

- [01 · MCP 是什么](docs/01-what-is-mcp.md)
- [02 · 第一个服务器](docs/02-first-server.md)
- [03 · 工具设计](docs/03-tool-design.md)
- [04 · 安全边界](docs/04-security.md)
- [05 · 测试与接入](docs/05-testing.md)

## 许可证

[MIT](LICENSE)。样例文档为合成内容，不含任何真实业务数据。
