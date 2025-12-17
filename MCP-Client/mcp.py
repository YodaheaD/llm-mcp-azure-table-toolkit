# mcp.py
import requests
from typing import Dict, Any

MCP_SERVER_URL = "http://localhost:3333/mcp"


def call_mcp_tool(tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "tool": tool,
        "arguments": arguments,
    }

    resp = requests.post(MCP_SERVER_URL, json=payload)
    resp.raise_for_status()

    return resp.json()
