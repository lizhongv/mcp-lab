# 贡献指南

感谢你对 MCP Lab 的关注。这个仓库的定位是「小而完整」：用尽量少、尽量易读的代码，把 MCP 服务器的构建、边界与测试讲清楚。提交改动前，请先读完本文。

## 提交 Issue

- **缺陷**：说明版本（`uv run python -m clients.cli --version`）、平台、复现步骤、期望结果与实际结果，附上报错信息。请删除日志中的 API Key。
- **功能建议**：说明使用场景、期望的工具形态与安全边界；较大的功能请先在 Issue 中讨论。

## 开发环境

需要 Python 3.10+ 与 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync                 # 安装依赖（含开发工具）
uv run pytest -q        # 运行测试
uv run ruff check .     # 代码检查
uv run python -m clients.cli --server kb
```

测试不需要 API Key，也不访问外网。

## 代码规范

- 遵循 PEP 8，由 ruff 检查，单行不超过 119 字符。
- 公开函数写类型注解与中文文档字符串；注释说明「为什么」，不复述代码。
- **业务逻辑放 `core.py`，MCP 绑定放 `server.py`**：前者可单测，后者只做协议适配。
- 工具描述必须写清「做什么、参数边界、返回什么」；错误返回可读的原因码。
- 涉及文件、网络、命令的能力必须同时提交安全测试。
- 新依赖要克制：优先标准库或已有依赖。

## 新增一个服务器

1. 建 `servers/<name>/core.py` 与 `server.py`，在 `clients/cli.py` 的 `SERVERS` 中登记模块名；
2. 至少提供 2 个工具，并在描述中写清参数边界；
3. 在 `tests/` 增加核心层单元测试与一个协议级测试；
4. 更新 README 的服务器表、目录结构与路线图；
5. 若有安全边界，更新 `docs/04-security.md` 与 `SECURITY.md`。

## 提交规范

使用约定式提交：

```
feat(kb): 增加按标题检索
fix(files): 拒绝指向根目录外的符号链接
docs: 补充 SSRF 防护说明
test(fetch): 覆盖重定向不跟随
```

一个提交只做一件事；代码、测试与文档同步提交。

## Pull Request

1. 从 `main` 新建分支，命名如 `feat/git-server`、`fix/path-escape`；
2. 本地通过 `uv run ruff check .` 与 `uv run pytest -q`；
3. 在 PR 描述中说明动机、改动范围与验证方式；
4. CI 全绿后再请求评审。

## 发布流程

1. 更新 `pyproject.toml`、`shared/__init__.py` 的版本号与 `CHANGELOG.md`；
2. 提交后打 `vX.Y.Z` 标签并推送；
3. `release` 工作流会运行测试、构建 wheel 与源码包，并按 CHANGELOG 生成 Release。
