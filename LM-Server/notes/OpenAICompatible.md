Target API (What Clients Expect)

Endpoint:

POST /v1/chat/completions

Request (example):

{
  "model": "local-llama",
  "messages": [
    { "role": "system", "content": "You are helpful" },
    { "role": "user", "content": "Explain MCP servers" }
  ],
  "stream": true,
  "max_tokens": 150
}

Response:

Non-streaming → one JSON blob

Streaming → SSE chunks (chat.completion.chunk)

This is exactly what OpenAI does.

## Understanding the Mapping 

Chat models are just prompt builders.
The process is: messages[] → internal prompt -> token loop

We must:
1. Convert messages[] → a single prompt string

2. Feed that prompt to llama.cpp

3. Wrap output in OpenAI-shaped JSON