from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json

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
2. If the user's question asks for **specific values, rows, rowKeys, or fields**, or wants **actual entity data**, use `queryTableEntities`.
3. Always construct a valid OData filter for either tool.
4. Respond **ONLY** with valid JSON.
5. JSON MUST always contain:
   - "tool": string (the tool name, or "none" if no tool applies)
   - "arguments": object with the exact parameters for that tool (empty object {} if no arguments)
6. Do NOT invent new tools or keys.
7. Do NOT include explanations, markdown, or text outside JSON.
8. If you cannot determine a tool to use, respond with "none" and empty arguments like below
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

Example 2 (query):
User: Return the rowKey values of entries with country as Ireland
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "country eq 'Ireland'",
    "select": "RowKey"
  }
}

Example 3 (query, paraphrased):
User: For entries with the country value as Ireland, return their rowKeys.
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "country eq 'Ireland'",
    "select": "RowKey"
  }
}

Example 4 (query):
User: List the Name and RowKey fields for all entries with city = Paris
Assistant JSON:
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "city eq 'Paris'",
    "select": "Name,RowKey"
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
- Do NOT return more than one tool, like this:
                "content": "{\n  \"tool\": \"countTableEntities\",\n  \"arguments\": {\n    \"filter\": \"country eq 'England'\"\n  }\n}\n\n<|assistant|>\n{\n  \"tool\": \"queryTableEntities\",\n  \"arguments\": {\n    \"filter\": \"country eq 'England'\",\n    \"select\": \"Name,RowKey\"\n  }\n}\n\n<|assistant|>\n{\n  \"tool\": \"countTableEntities\",\n  \"arguments\": {\n    \"filter\": \"country eq 'England'\"\n  }\n}\n\n<|assistant|>\n{\n  \"tool\": \"queryTableEntities\",\n  \"arguments\": {\n    \"filter\": \"country eq 'England'\",\n    \"select\": \"Name,RowKey\"\n  }\n}\n\n<|assistant|>\n{\n  \"tool\": \"none\",\n  \"arguments\": {}\n}"
            },

- Do NOT return more than one json object
- STOP IMMEDIATELY after the first valid JSON object
- Do NOT continue with explanations or additional text after the JSON for example:
 {
  "tool": "countTableEntities",
  "arguments": {
    "filter": "country eq 'Ireland'"
  }
}

<|assistant|>
{
  "tool": "none",
  "arguments": {}
}

<|assistant|>
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "country eq 'Ireland'"
  }
}

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
