"""MCP Lab 的共用工具：路径沙箱与统一的工具错误。"""

from .errors import ToolError
from .paths import ensure_dir, safe_path

__version__ = "1.0.0"

__all__ = ["ToolError", "ensure_dir", "safe_path"]
