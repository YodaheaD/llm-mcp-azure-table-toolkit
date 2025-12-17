# Walkthrough of the Proect starting from a User Question
This walkthrough explains how a user question is processed step-by-step through the MCP Client, LM Server, and MCP Server to produce a final answer.

> **“How many entities have city as Atlanta?”**

---

## 1️⃣ User → MCP Client

The user types:

```
How many entities have city as Atlanta?
```

The **MCP Client** is the entry point.
It does **not** query data and does **not** reason about the answer.

Its job is orchestration.

---

## 2️⃣ MCP Client → LM Server (tool selection)

The MCP Client sends the question to the **LM Server** with a strict system prompt that explains:

* What tools exist
* When to use them
* That the response must be JSON

**Request sent to LM Server**

```
POST /v1/chat/completions
```

Payload (simplified):

```json
{
  "messages": [
    { "role": "system", "content": "You are a tool-using assistant..." },
    { "role": "user", "content": "How many entities have city as Atlanta?" }
  ]
}
```

---

## 3️⃣ LM Server → MCP Client (tool decision)

The **LM Server**:

* Understands the question
* Detects a **count request**
* Chooses the correct tool

It returns **only a tool call**:

```json
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "city eq 'Atlanta'"
  }
}
```

⚠️ Important:

* No database access happened
* No data was hallucinated
* This is just an **instruction**

---

## 4️⃣ MCP Client validates the tool call

The MCP Client:

* Parses the JSON
* Validates it against a schema
* Confirms the tool name is allowed

If validation fails → stop
If valid → continue

---

## 5️⃣ MCP Client → MCP Server (execute tool)

The MCP Client forwards the tool call to the **MCP Server**:

```
POST http://localhost:3333/mcp
```

Body:

```json
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "city eq 'Atlanta'"
  }
}
```

---

## 6️⃣ MCP Server → Azure Table Storage

The **MCP Server**:

* Maps `countTableEntities` to real Python code
* Runs a real Azure Table Storage query
* Counts matching entities

Internally:

```python
query_entities("city eq 'Atlanta'")
```

---

## 7️⃣ MCP Server → MCP Client (raw result)

The MCP Server returns a deterministic response:

```json
{
  "content": [
    {
      "type": "text",
      "text": "The Azure Table \"mainData\" contains 185 entities matching filter: \"city eq 'Atlanta'\"."
    }
  ]
}
```

This is **trusted data**.

---

## 8️⃣ MCP Client → LM Server (finalization)

The MCP Client sends a follow-up to the **LM Server**, including:

* Original question
* The tool call it made
* The tool result

This tells the model:

> “The data is real — explain it.”

---

## 9️⃣ LM Server → MCP Client (final answer)

The LM Server converts the tool result into a clean response:

```
The Azure Table contains 185 entities with city equal to Atlanta.
```

No tools are called here.

---

## 🔟 MCP Client → User

The MCP Client prints the final answer.

The request lifecycle is complete.

---

## Mental Model (Simple)

```
User
 ↓
MCP Client
 ↓
LM Server (decides tool)
 ↓
MCP Client
 ↓
MCP Server (executes query)
 ↓
MCP Client
 ↓
LM Server (formats answer)
 ↓
User
```

---

## Why This Works So Well

* The LLM **never touches your data**
* The database **never trusts the LLM**
* Every step is auditable
* Hallucinations are structurally minimized

A **production-grade agent system** — locally.

