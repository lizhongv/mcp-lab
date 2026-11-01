# 01 · MCP 是什么

MCP（Model Context Protocol）是一套让模型调用外部能力的协议。它把系统分成三个角色：

- **Host**：承载模型的程序，例如 Claude Code、知源，或你自己的客户端。
- **Client**：Host 内部与某个服务器保持连接的组件，负责握手与调用。
- **Server**：提供工具（tools）、资源（resources）和提示（prompts）的进程。

## 一次工具调用的路径

```
Host/Client                      Server
    |  initialize  ------------->  |
    |  <------------- capabilities |
    |  tools/list  ------------->  |
    |  <------------- tool schema  |
    |  tools/call  ------------->  |
    |  <------------- result       |
```

服务器可以是本地进程（stdio），也可以是远程服务（Streamable HTTP）。本实验室全部用 stdio：客户端拉起子进程，通过标准输入输出交换 JSON-RPC。

## tools、resources、prompts 的区别

- **tool**：有副作用的动作或需要参数的计算，例如检索、读文件、发请求；
- **resource**：可被读取的静态内容，例如 `kb://doc/1`；
- **prompt**：预置的提示模板，供 Host 选择使用。

初学阶段把一切都做成 tool 是可以的，但读多写少的内容更适合 resource。

## 为什么服务器要自己校验

模型看到的是工具描述，不是你的代码。提示词注入可以让它请求 `../../etc/passwd`、内网地址或危险命令。**客户端会做一部分拦截，但服务器不能假设客户端一定拦得住**。路径、网络、命令三类工具尤其要在服务端做边界检查，这就是第 04 章的内容。

下一章：[02 · 第一个服务器](02-first-server.md)
