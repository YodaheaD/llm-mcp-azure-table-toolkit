import asyncio
from MCP_Client.client import call_tool
# call_tool location: C:\Users\yodah\CodeWorkNew\MCP_Project\LLM-Top-Down\MCP-Client\client.py

async def run_tool(tool_name: str, arguments: dict):
    return await call_tool(tool_name, arguments)
