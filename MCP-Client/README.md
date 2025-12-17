# MCP-Client: Model Context Protocol Client

## Overview

MCP-Client is the orchestration layer of the LLM Top-Down architecture. It acts as middleware between the LM-Server (language model) and MCP-Server (data tools), coordinating tool calls and managing the flow of information. The client interprets LLM responses, validates tool calls, and formats results back to the user.

## Features

### 🔄 Core Orchestration
- **Tool Call Detection**: Parses LLM responses for JSON tool calls
- **Validation Pipeline**: Pydantic-based tool call validation
- **Error Handling**: Graceful fallback for invalid responses
- **Response Formatting**: Clean output formatting and display

### 🛠️ Tool Management
- **Dynamic Tool Routing**: Routes calls to appropriate MCP servers
- **Schema Validation**: Ensures tool arguments match expected formats
- **Result Processing**: Formats tool results for user consumption
- **System Prompt Management**: Configurable tool instructions

### 🔗 Integration Layer
- **LM-Server Communication**: Seamless chat completion requests
- **MCP-Server Integration**: Direct tool execution via HTTP API
- **JSON Protocol**: Structured communication between components

## Architecture

```
User Question
     |
     v
┌─────────────────┐
│   MCP-Client    │
│                 │
│ ┌─────────────┐ │    ┌─────────────────┐
│ │ LLM_Script  │◄├───►│   LM-Server     │
│ └─────────────┘ │    └─────────────────┘
│        │        │
│        v        │
│ ┌─────────────┐ │    ┌─────────────────┐
│ │ Tool Parser │◄├───►│   MCP-Server    │
│ └─────────────┘ │    └─────────────────┘
└─────────────────┘
     |
     v
Formatted Response
```

## Installation

### Prerequisites
- Python 3.8+
- Running LM-Server instance
- Running MCP-Server instance

### Dependencies
```bash
pip install pydantic requests
```

### Package Configuration
The project includes a [`package.json`](package.json) for Node.js compatibility, though the core is Python-based.

## Configuration

### System Prompt
The system prompt in [`client.py`](client.py#L6-L18) defines available tools and behavior:

```python
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
```

### Server Endpoints
- **LM-Server**: `http://localhost:8000`
- **MCP-Server**: `http://localhost:8001`

## Usage

### Running the Client
```bash
# From project root
cd MCP-Client
python client.py
```

### Interactive Usage
The client processes questions through a three-step pipeline:

1. **LLM Query**: Send question to language model
2. **Tool Detection**: Parse response for tool calls
3. **Tool Execution**: Call MCP-Server if tools needed

### Example Interactions

#### Direct Question (No Tools)
```python
question = "What is machine learning?"
# Returns: Direct LLM response (no tool call)
```

#### Tool-Required Question
```python
question = "How many entities are in the Azure table?"
# Process:
# 1. LLM determines tool needed: countTableEntities
# 2. Client calls MCP-Server
# 3. Returns: "The Azure Table 'mainData' contains X entities"
```

#### Complex Query
```python
question = "Show me the first 5 records where status is active"
# Process:
# 1. LLM determines tool: queryTableEntities
# 2. Arguments: {"filter": "status eq 'active'", "top": 5}
# 3. Returns: Formatted query results
```

## File Structure

```
MCP-Client/
├── client.py         # Main orchestration logic
├── LLM_Script.py     # LM-Server communication
├── mcp.py            # MCP-Server communication
├── schemas.py        # Pydantic validation models
├── package.json      # Node.js package configuration
├── __pycache__/      # Python cache
└── README.md         # This file
```

## Core Components

### client.py
Main orchestration logic:

```python
def run(question: str):
    # 1. Query LLM
    messages = [...]
    raw_response = call_llm(messages)
    
    # 2. Parse tool call
    try:
        tool_call = ToolCall.model_validate(json.loads(raw_response))
    except (json.JSONDecodeError, ValidationError):
        return raw_response  # Direct response
    
    # 3. Execute tool
    tool_result = call_mcp_tool(tool_call.tool, tool_call.arguments)
    return format_response(tool_result)
```

### LLM_Script.py
Handles communication with LM-Server:

```python
def call_llm(messages: list) -> str:
    # Sends chat completion request to LM-Server
    # Returns raw text response
```

### mcp.py
Manages MCP-Server tool calls:

```python
def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    # Routes tool calls to appropriate MCP-Server endpoint
    # Returns structured tool results
```

### schemas.py
Pydantic models for validation:

```python
class ToolCall(BaseModel):
    tool: str                    # Tool name
    arguments: Dict[str, Any]    # Tool arguments
```

## Available Tools

The client currently supports Azure Table operations:

### countTableEntities
**Purpose**: Count entities in Azure table

**Arguments**:
- `filter` (optional): OData filter expression

**Example**:
```json
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "status eq 'active'"
  }
}
```

### queryTableEntities
**Purpose**: Query and retrieve table entities

**Arguments**:
- `filter` (optional): OData filter expression
- `top` (optional): Number of results to return
- `select` (optional): Columns to include

**Example**:
```json
{
  "tool": "queryTableEntities",
  "arguments": {
    "filter": "partitionKey eq 'user'",
    "top": 10,
    "select": "name,status"
  }
}
```

## Development

### Adding New Tools

1. **Update System Prompt**
   ```python
   SYSTEM_PROMPT = """
   Available tools:
   - countTableEntities
   - queryTableEntities
   - newToolName        # Add here
   """
   ```

2. **Add Tool Logic**
   ```python
   # In mcp.py
   def call_mcp_tool(tool_name: str, arguments: dict):
       if tool_name == "newToolName":
           # Handle new tool
       # ... existing logic
   ```

3. **Update Schemas**
   ```python
   # In schemas.py
   # Add any new validation models if needed
   ```

### Testing

```python
# Test direct LLM response
response = run("What is Python?")
print(response)

# Test tool calling
response = run("Count all table entries")
print(response)
```

### Debugging

The client outputs detailed logs:
```
LLM RAW RESPONSE:
{"tool": "countTableEntities", "arguments": {}}

TOOL RESULT:
{"content": [{"type": "text", "text": "The Azure Table..."}]}
```

## Error Handling

### Invalid JSON Response
- **Scenario**: LLM returns non-JSON text
- **Action**: Return direct response (no tool call)

### Validation Errors
- **Scenario**: JSON doesn't match ToolCall schema
- **Action**: Fallback to direct response

### Tool Execution Errors
- **Scenario**: MCP-Server returns error
- **Action**: Format error message for user

### Network Issues
- **Scenario**: Cannot reach LM-Server or MCP-Server
- **Action**: Display connection error

## Performance Considerations

### Response Time
- LLM inference: ~1-3 seconds
- Tool execution: ~0.5-1 seconds
- Total pipeline: ~2-4 seconds

### Optimization Tips
- Keep system prompts concise
- Use efficient tool argument validation
- Cache common tool results if applicable

## Integration Patterns

### With LM-Server
```python
# Standard chat completion
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": question}
]
response = call_llm(messages)
```

### With MCP-Server
```python
# Tool execution
result = call_mcp_tool(
    tool_name="countTableEntities",
    arguments={"filter": "status eq 'active'"}
)
```

## Troubleshooting

### Common Issues

1. **Tools Not Detected**
   - Check system prompt format
   - Verify LLM understands tool syntax
   - Review JSON parsing logic

2. **Tool Execution Fails**
   - Ensure MCP-Server is running
   - Verify tool arguments format
   - Check network connectivity

3. **Response Formatting Issues**
   - Validate Pydantic models
   - Check JSON structure
   - Review error logs

## Contributing

When modifying MCP-Client:
1. Maintain clear separation between LLM and tool logic
2. Add validation for new tool schemas
3. Test both direct and tool-based responses
4. Update system prompts appropriately

---

**Next Steps**: Configure tool endpoints and test the complete pipeline with both LM-Server and MCP-Server running.