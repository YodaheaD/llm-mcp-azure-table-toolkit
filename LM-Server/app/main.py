from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re


# --------------------------
# Model Configuration
# --------------------------
MODEL_PATH = r"C:\Users\yodah\.cache\lm-studio\models\hugging-quants\Llama-3.2-1B-Instruct-Q8_0-GGUF\llama-3.2-1b-instruct-q8_0.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=8,
)

app = FastAPI()
# --------------------------
# CORS Configuration
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------
# Basic Generation (non-chat)
# --------------------------
class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    text: str

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    output = llm(
        req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return {"text": output["choices"][0]["text"]}

@app.post("/generate/stream")
def generate_stream(req: GenerateRequest):
    def event_generator():
        for chunk in llm(
            req.prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            stream=True,
        ):
            token = chunk["choices"][0]["text"]
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )

# --------------------------
# OpenAI-Compatible Chat API
# --------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 256
    temperature: float = 0.2
    stream: Optional[bool] = False

# --------------------------
# MCP-Aware System Prompt
# --------------------------
SYSTEM_TOOL_PROMPT = """
You are a tool-using assistant.

Available tools:

1. countTableEntities
   - Purpose: Count entities in an Azure Table Storage table.
   - Arguments:
     {
       "filter": "OData filter string (example: city eq 'Atlanta')"
     }

2. queryTableEntities
   - Purpose: Retrieve entities from an Azure Table Storage table.
   - Arguments:
     {
       "filter": "OData filter string (example: city eq 'Atlanta')",
       "top": "Optional, number of entities to return (default: 100)",
       "select": "Optional, comma-separated list of fields to include"
     }

Rules for choosing the tool:

1. If the user's question asks for a **count**, **total number**, or any summary/statistical number, use `countTableEntities`.
2. If the user's question asks for **specific values, rows, rowKeys, fields, or examples**, use `queryTableEntities`.
3. If the user specifies a **number of results** (numeric or verbal), you MUST set `top` to that number.
   - Examples of quantity signals: numbers (5, 10), words (five, ten), phrases like "first 3", "only 2", "give me 7".
4. If no number is specified, omit `top` and allow the default behavior.
5. Always construct a valid OData filter.
6. Respond **ONLY** with valid JSON.
7. JSON MUST always contain:
   - "tool": string (the tool name, or "none" if no tool applies)
   - "arguments": object with the exact parameters for that tool (empty object {} if no arguments)
8. Do NOT invent new tools or keys.
9. Do NOT include explanations, markdown, or text outside JSON.
10. If you cannot determine a tool to use, respond with "none" and empty arguments like below:
{
  "tool": "none",
  "arguments": {}
}

Few-shot examples:

Example 1 (count):
User: How many entries in our table have city as Atlanta?
Assistant JSON:
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "city eq 'Atlanta'"
  }
}

Example 2 (query, all results):
User: Return the rowKey values of entries with country as Ireland
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "country eq 'Ireland'",
    "select": "RowKey"
  }
}

Example 3 (query with explicit quantity):
User: Give me five rowKeys for entries with city as Tokyo
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "city eq 'Tokyo'",
    "select": "RowKey",
    "top": 5
  }
}

Example 4 (query, paraphrased quantity):
User: I only want 3 Name values for entries where city is Paris
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "city eq 'Paris'",
    "select": "Name",
    "top": 3
  }
}

Example 5 (no tool needed):
User: Say hello to me
Assistant JSON:
{
  "tool": "none",
  "arguments": {}
}

Common Mistakes to Avoid:
- Do NOT return more than one JSON object.
- Do NOT omit `top` when the user specifies a quantity.
- Do NOT return explanations or text outside JSON.
- STOP IMMEDIATELY after the first valid JSON object.

IMPORTANT:
- When calling a tool, respond with EXACTLY ONE JSON object.
- STOP immediately after the JSON.
- Do NOT continue the conversation.
- Do NOT add another assistant response.
"""


def messages_to_prompt(messages: List[ChatMessage]) -> str:
    prompt = "<|system|>\n" + SYSTEM_TOOL_PROMPT.strip() + "\n"

    for msg in messages:
        if msg.role == "system":
            prompt += f"\n{msg.content}\n"
        elif msg.role == "user":
            prompt += f"<|user|>\n{msg.content}\n"
        elif msg.role == "assistant":
            prompt += f"<|assistant|>\n{msg.content}\n"

    prompt += "<|assistant|>\n"
    return prompt

# --------------------------
# Chat Completion Endpoint
# --------------------------
@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    prompt = messages_to_prompt(req.messages)

    # -------- Non-streaming --------
    if not req.stream:
        output = llm(
            prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )

        text = output["choices"][0]["text"]

        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": text,
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    # -------- Streaming (SSE) --------
    def event_generator():
        for chunk in llm(
            prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            stream=True,
        ):
            token = chunk["choices"][0]["text"]
            if not token:
                continue

            payload = {
                "id": "chatcmpl-local",
                "object": "chat.completion.chunk",
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None,
                    }
                ],
            }

            yield f"data: {json.dumps(payload)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )

def infer_top_from_prompt(prompt: str):
    match = re.search(r'\b(\d+)\b', prompt)
    if match:
        return int(match.group(1))
    return None
# --------------------------
# Chat Endpoint Integrating LLM and MCP-Server
# --------------------------
@app.post("/chat")
async def chat(request: Request):
    """
    Receives a user prompt, calls LLM to get MCP tool JSON,
    then calls MCP-Server to execute tool, returns final result to UI.
    """
    body = await request.json()
    prompt = body.get("input")

    if not prompt:
        raise HTTPException(status_code=400, detail="Missing input")

    # Wrap prompt in a ChatMessage
    messages = [ChatMessage(role="user", content=prompt)]
    llm_prompt = messages_to_prompt(messages)

    # Call LLM
    output = llm(
        llm_prompt,
        max_tokens=256,
        temperature=0.2,
    )
    llm_text = output["choices"][0]["text"].strip()

    # Parse tool JSON
    try:
        tool_json = json.loads(llm_text)
    except json.JSONDecodeError:
        return {"response": f"LLM returned invalid JSON:\n{llm_text}"}

    tool_name = tool_json.get("tool", "none")
    arguments = tool_json.get("arguments", {})

    if tool_name == "none":
        return {"response": "No tool execution required."}

    # Manually infer and set top parameter if needed
    user_top = infer_top_from_prompt(prompt)
    
    if tool_name == "queryTableEntities" and user_top is not None:
        arguments["top"] = user_top

    # Call MCP-Server to execute tool
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:3333/mcp", json={
                "tool": tool_name,
                "arguments": arguments
            })
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as e:
            return {"response": f"Error calling MCP-Server: {str(e)}"}

    # Return MCP result to UI
    return {"response": result}