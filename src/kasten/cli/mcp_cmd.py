"""MCP server command — start the kasten MCP server for agent integration."""

from __future__ import annotations

import sys


def mcp() -> None:
    """Start the MCP server (stdio transport) for Claude Desktop, Cursor, etc.

    Requires: pip install llm-kasten[mcp]
    """
    try:
        from kasten.mcp.server import server
    except ImportError:
        print("MCP server requires: pip install llm-kasten[mcp]", file=sys.stderr)
        sys.exit(1)

    server.run()
