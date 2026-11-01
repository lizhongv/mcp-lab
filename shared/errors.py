"""工具错误：给模型返回可读的失败原因，而不是抛裸异常。"""


class ToolError(Exception):
    """可预期的工具调用失败。

    MCP 服务器应把这类错误转成工具错误返回，让模型知道「参数不对/越权」，
    而不是让它猜服务器是不是挂了。
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
