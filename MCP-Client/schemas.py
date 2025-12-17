# schemas.py
from pydantic import BaseModel
from typing import Dict, Any, Literal


class ToolCall(BaseModel):
    tool: Literal["countTableEntities", "queryTableEntities"]
    arguments: Dict[str, Any]
