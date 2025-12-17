# client.py
import json
from LLM_Script import call_llm
from mcp import call_mcp_tool
from schemas import ToolCall
from pydantic import ValidationError

SYSTEM_PROMPT = """
You are a tool-using assistant.

Available tools:
- countTableEntities
- queryTableEntities

Rules:
- Respond ONLY with valid JSON when calling a tool
- JSON must contain "tool" and "arguments"
- NEVER invent data values
- NEVER return table data directly
- Always delegate table access to tools
"""

def run(question: str):
    # -----------------------------
    # 1. Ask the LLM what to do
    # -----------------------------
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    raw_response = call_llm(messages)
    print("\nLLM RAW RESPONSE:\n", raw_response)

    # -----------------------------
    # 2. Try parsing as tool call
    # -----------------------------
    try:
        tool_call = ToolCall.model_validate(json.loads(raw_response))
    except (json.JSONDecodeError, ValidationError):
        # No tool needed → return LLM response directly
        return raw_response

    # -----------------------------
    # 3. Call MCP Server
    # -----------------------------
    tool_result = call_mcp_tool(
        tool_call.tool,
        tool_call.arguments,
    )

    # -----------------------------
    # 4. FINAL ANSWER = MCP RESULT
    # -----------------------------
    return tool_result


if __name__ == "__main__":
    while True:
        q = input("\nAsk a question, prompt (or 'exit'): ")
        if q.lower() == "exit":
            break

        answer = run(q)
        print("\nFINAL ANSWER:\n", answer)
