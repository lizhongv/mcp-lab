"""网页抓取测试：本地起一个 HTTP 服务，验证解析与 SSRF 防护。"""

from __future__ import annotations

import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from servers.fetch import core
from shared.errors import ToolError


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"<html><body><h1>Hello</h1><script>bad()</script><p>world</p></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # noqa: ANN002
        return


@pytest.fixture
def local_url():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_html_to_text() -> None:
    text = core.html_to_text("<p>a</p><script>x</script><p>b</p>")
    assert "a" in text and "b" in text and "x" not in text


def test_fetch_local_with_allow_private(local_url: str) -> None:
    result = asyncio.run(core.fetch_url(local_url, allow_private=True))
    assert result["status"] == 200
    assert "Hello" in result["text"] and "world" in result["text"]
    assert "bad()" not in result["text"]


def test_private_address_is_blocked_by_default(local_url: str) -> None:
    with pytest.raises(ToolError) as error:
        asyncio.run(core.fetch_url(local_url))
    assert error.value.code == "PRIVATE_ADDRESS"


def test_invalid_scheme() -> None:
    with pytest.raises(ToolError) as error:
        asyncio.run(core.fetch_url("file:///etc/passwd"))
    assert error.value.code == "INVALID_URL"
