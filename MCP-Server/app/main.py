# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from utils.azure_table import get_table_client
import os
import logging
from datetime import datetime

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO)

# --------------------------
# FastAPI App
# --------------------------
app = FastAPI()

# --------------------------
# Pydantic Request Model
# --------------------------
class MCPRequest(BaseModel):
    tool: str
    arguments: Optional[Dict[str, Any]] = None
    args: Optional[Dict[str, Any]] = None

# --------------------------
# MCP Tools
# --------------------------
async def count_table_entities(filter: Optional[str] = None):
    async with await get_table_client() as table_client:
        count = 0
        logging.info(f"Counting entities with filter: {filter}")

        async for _ in table_client.query_entities(query_filter=filter):
            count += 1

    return {
        "content": [
            {
                "type": "text",
                "text": f'The Azure Table "mainData" contains {count} entities matching filter: "{filter or "none"}".'
            }
        ]
    }


async def query_table_entities(filter: Optional[str] = None, top: Optional[int] = 100, select: Optional[str] = None):
    async with await get_table_client() as table_client:
        results = []
        count = 0
        max_results = top or 100

        logging.info(f"Querying table with filter: {filter}, top={max_results}, select={select}")

        async for entity in table_client.query_entities(
            query_filter=filter,
            select=[s.strip() for s in select.split(",")] if select else None
        ):
            if count >= max_results:
                break
            results.append(entity)
            count += 1

    return {
        "content": [
            {
                "type": "text",
                "text": str({
                    "table": "mainData",
                    "filter": filter or "none",
                    "top": max_results,
                    "select": select or "all",
                    "resultCount": count,
                    "entities": results,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        ]
    }


tools = {
    "countTableEntities": count_table_entities,
    "queryTableEntities": query_table_entities,
}

# --------------------------
# HTTP Endpoint
# --------------------------
@app.post("/mcp")
async def mcp_tool(req: MCPRequest):
    args = req.arguments or req.args or {}

    tool_name = req.tool
    if not tool_name or tool_name not in tools:
        raise HTTPException(status_code=400, detail=f'Tool "{tool_name}" not found.')

    # Ensure filter is string or None
    if "filter" in args and args["filter"] is None:
        args["filter"] = None

    try:
        logging.info(f"MCP Tool Call: {tool_name} {args}")
        result = await tools[tool_name](**args)
        return result
    except Exception as e:
        logging.error("ERROR OCCURRED", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------
# Run Server (uvicorn)
# --------------------------
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 3333))
    logging.info(f"✅ MCP Server running on http://localhost:{PORT}/mcp")
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
