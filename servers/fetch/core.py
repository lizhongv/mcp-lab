"""网页抓取核心：带 SSRF 防护与响应大小限制。"""

from __future__ import annotations

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from shared.errors import ToolError

ALLOWED_TYPES = ("text/html", "text/plain", "application/json", "application/xml", "text/xml")
MAX_BYTES = 1024 * 1024
TIMEOUT = 10.0


class _TextExtractor(HTMLParser):
    """极简 HTML 转文本：跳过 script/style，保留可读文字。"""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return "\n".join(parser.parts)


def _check_host(host: str, port: int, allow_private: bool) -> None:
    if allow_private:
        return
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ToolError("DNS_ERROR", f"无法解析域名：{host}") from error
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ToolError("PRIVATE_ADDRESS", f"{host} 解析到内网地址 {ip}，已拒绝（SSRF 防护）")


async def fetch_url(url: str, max_chars: int = 8000, allow_private: bool = False) -> dict:
    """抓取一个公开网页并转成纯文本；不跟随重定向。"""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ToolError("INVALID_URL", "只支持 http / https")
    if not parsed.hostname:
        raise ToolError("INVALID_URL", "缺少主机名")
    if parsed.username or parsed.password:
        raise ToolError("INVALID_URL", "URL 不能包含用户名或密码")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    _check_host(parsed.hostname, port, allow_private)

    max_chars = max(200, min(max_chars, 50000))
    async with (
        httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client,
        client.stream("GET", url) as response,
    ):
            if response.status_code in (301, 302, 303, 307, 308):
                return {
                    "url": url,
                    "status": response.status_code,
                    "location": response.headers.get("location", ""),
                    "note": "出于 SSRF 防护不自动跟随重定向，请手动确认目标地址",
                }
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            if content_type not in ALLOWED_TYPES:
                raise ToolError("UNSUPPORTED_TYPE", f"不支持的内容类型：{content_type or '未知'}")

            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) >= MAX_BYTES:
                    break
            text = bytes(body[:MAX_BYTES]).decode(response.encoding or "utf-8", "replace")
            text = html_to_text(text) if content_type == "text/html" else text.strip()

    truncated = len(text) > max_chars
    return {
        "url": url,
        "status": response.status_code,
        "content_type": content_type,
        "text": text[:max_chars],
        "truncated": truncated,
    }
