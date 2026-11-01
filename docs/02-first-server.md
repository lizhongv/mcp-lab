# 02 · 第一个服务器

本章以 `servers/kb` 为例，说明一个 MCP 服务器的最小结构。

## 业务逻辑与协议绑定分开

```
servers/kb/
├── core.py     纯 Python：连接 SQLite、检索、读文档
└── server.py   FastMCP：把 core 的函数注册成工具
```

好处：`core.py` 可以用普通单元测试覆盖，不需要启动 MCP 协议；`server.py` 只负责协议层，失败时容易定位。

## 注册一个工具

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kb")

@mcp.tool()
def search(query: str, limit: int = 5) -> list[dict]:
    """按关键词检索知识库，返回编号、标题、摘要与相关度分数。

    Args:
        query: 检索词。
        limit: 返回条数，1～20。
    """
    return core.search_documents(conn, query, limit)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

工具的名字、描述与参数类型会被 SDK 转成 JSON Schema 发给客户端。**描述就是模型的使用说明**：写清楚「做什么、参数是什么、返回什么」，模型才不容易乱调。

## 本地数据

`core.connect()` 打开 `data/kb.sqlite`，空库时从 `data/samples/*.md` 导入三篇合成文档。检索优先用 FTS5 的 trigram 分词；查询短于 3 个字符时退回 `LIKE`，保证中文双字词也能命中。

## 验证

```bash
uv run python -m clients.cli --server kb
uv run python -m clients.cli --server kb --tool search --args '{"query":"MCP"}'
```

或者用 Inspector：

```bash
npx -y @modelcontextprotocol/inspector uv run python -m servers.kb.server
```

## 练习

1. 增加一个 `search_by_title` 工具，只匹配标题；
2. 给 `list_documents` 增加 `offset` 参数并在描述里写清楚分页语义；
3. 思考：`get_document` 返回全文，文档很大时应该怎么截断？

下一章：[03 · 工具设计](03-tool-design.md)
