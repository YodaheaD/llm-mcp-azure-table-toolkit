# MCP-Server: Model Context Protocol Server

## Overview

MCP-Server is a FastAPI-based server that implements the Model Context Protocol for Azure Table Storage integration. It provides RESTful endpoints for querying, counting, and managing Azure Table entities, serving as the data layer for the LLM Top-Down architecture.

## Features

### 🗄️ Azure Table Integration
- **Async Operations**: High-performance async Azure SDK integration
- **Entity Querying**: Flexible OData filtering and pagination
- **Count Operations**: Efficient entity counting with filters
- **Connection Management**: Secure Azure Storage connection handling

### 🔧 MCP Protocol Support
- **JSON API**: Clean JSON request/response format
- **Tool Abstraction**: High-level tool interface for complex operations
- **Error Handling**: Comprehensive error reporting and logging
- **Type Safety**: Full Pydantic validation for requests

### ⚡ Performance Features
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient Azure client management
- **Pagination Support**: Large dataset handling
- **Selective Queries**: Column-specific data retrieval

## Installation

### Prerequisites
- Python 3.8+
- Azure Storage Account
- Azure Table with data

### Dependencies
```bash
pip install fastapi azure-data-tables uvicorn pydantic
```

### Azure Setup
1. Create an Azure Storage Account
2. Create a table named `mainData` (or update `FIXED_TABLE_NAME`)
3. Populate with sample data
4. Get the connection string

## Configuration

### Azure Connection
Update the connection string in [`utils/azure_table.py`](utils/azure_table.py#L8):

```python
connection_string = "DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net;"
```

**⚠️ Security Note**: Use environment variables for production:
```python
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
```

### Table Configuration
```python
# In utils/azure_table.py
FIXED_TABLE_NAME = "mainData"  # Update if using different table
```

## Usage

### Starting the Server
```bash
# From project root
cd MCP-Server
uvicorn app.main:app --reload --port 8001
```

### API Endpoints

#### MCP Tool Execution
**Endpoint**: `POST /mcp`

**Purpose**: Execute MCP tools via unified interface

**Request Format**:
```json
{
  "tool": "countTableEntities",
  "arguments": {
    "filter": "status eq 'active'"
  }
}
```

**Response Format**:
```json
{
  "content": [
    {
      "type": "text", 
      "text": "The Azure Table 'mainData' contains 42 entities matching filter: 'status eq 'active''"
    }
  ]
}
```

## Available Tools

### countTableEntities
**Purpose**: Count entities in the Azure table

**Arguments**:
- `filter` (optional, string): OData filter expression

**Examples**:
```bash
# Count all entities
curl -X POST "http://localhost:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "countTableEntities",
       "arguments": {}
     }'

# Count with filter
curl -X POST "http://localhost:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "countTableEntities",
       "arguments": {
         "filter": "partitionKey eq 'users'"
       }
     }'
```

### queryTableEntities
**Purpose**: Query and retrieve table entities

**Arguments**:
- `filter` (optional, string): OData filter expression
- `top` (optional, int): Maximum number of entities (default: 100)
- `select` (optional, string): Comma-separated column names

**Examples**:
```bash
# Query all entities (limited to 100)
curl -X POST "http://localhost:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "queryTableEntities",
       "arguments": {}
     }'

# Query with filter and limit
curl -X POST "http://localhost:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "queryTableEntities",
       "arguments": {
         "filter": "status eq 'active'",
         "top": 10
       }
     }'

# Query specific columns
curl -X POST "http://localhost:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{
       "tool": "queryTableEntities",
       "arguments": {
         "select": "partitionKey,rowKey,name,status",
         "top": 5
       }
     }'
```

## OData Filter Examples

Azure Table Storage supports OData filtering:

### Basic Comparisons
```
status eq 'active'               # Equals
age gt 25                        # Greater than
createdDate lt datetime'2023-01-01T00:00:00Z'  # Less than
name ne 'admin'                  # Not equal
```

### Logical Operators
```
status eq 'active' and age gt 18         # AND
status eq 'active' or status eq 'pending' # OR
not (status eq 'inactive')               # NOT
```

### String Functions
```
startswith(name, 'John')         # Starts with
substringof('test', description) # Contains
```

## File Structure

```
MCP-Server/
├── app/
│   ├── main.py           # FastAPI application
│   ├── test/             # Unit tests
│   └── __pycache__/      # Python cache
├── utils/
│   ├── __init__.py       # Package initialization
│   ├── azure_table.py    # Azure Table client
│   ├── testQuery.py      # Query testing utility
│   └── __pycache__/      # Python cache
├── notes/
│   └── notes.md          # Development notes
└── README.md             # This file
```

## Core Implementation

### Main Application ([`app/main.py`](app/main.py))
```python
@app.post("/mcp")
async def handle_mcp_request(req: MCPRequest):
    """Unified MCP tool execution endpoint"""
    
    # Route to appropriate tool
    if req.tool == "countTableEntities":
        return await count_table_entities(...)
    elif req.tool == "queryTableEntities":
        return await query_table_entities(...)
    else:
        raise HTTPException(404, f"Unknown tool: {req.tool}")
```

### Azure Table Client ([`utils/azure_table.py`](utils/azure_table.py))
```python
async def get_table_client() -> TableClient:
    """Returns async TableClient for the fixed table"""
    connection_string = "..."
    client = TableClient.from_connection_string(connection_string, FIXED_TABLE_NAME)
    return client
```

### Request Model
```python
class MCPRequest(BaseModel):
    tool: str                           # Tool name
    arguments: Optional[Dict[str, Any]] = None  # Tool arguments
    args: Optional[Dict[str, Any]] = None       # Alternative argument field
```

## Development

### Testing
```bash
# Run query tests
cd utils
python testQuery.py

# Run unit tests
cd app/test
python -m pytest
```

### Adding New Tools

1. **Implement Tool Function**
   ```python
   async def new_tool_name(arg1: str, arg2: int = None):
       async with await get_table_client() as table_client:
           # Tool implementation
           return {"content": [{"type": "text", "text": "Result"}]}
   ```

2. **Add Route Handler**
   ```python
   @app.post("/mcp")
   async def handle_mcp_request(req: MCPRequest):
       # ... existing tools ...
       elif req.tool == "newToolName":
           return await new_tool_name(**arguments)
   ```

3. **Update Documentation**
   - Add tool description to README
   - Include example usage
   - Document arguments and responses

### Environment Variables
For production deployment:

```bash
# Set environment variables
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."
export TABLE_NAME="mainData"
export LOG_LEVEL="INFO"
```

## Monitoring and Logging

### Logging Configuration
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Key Log Messages
- Entity count operations
- Query filter applications
- Connection establishment
- Error conditions

### Health Check
The server automatically provides:
- `/docs` - Swagger UI documentation
- `/redoc` - ReDoc documentation
- Server status via FastAPI

## Error Handling

### Common Errors

1. **Connection Issues**
   ```python
   # Returns HTTP 500 with details
   {"detail": "Azure connection failed: [error details]"}
   ```

2. **Invalid Filter**
   ```python
   # Returns HTTP 400 with OData error
   {"detail": "Invalid filter expression: [details]"}
   ```

3. **Unknown Tool**
   ```python
   # Returns HTTP 404
   {"detail": "Unknown tool: invalidToolName"}
   ```

### Error Response Format
All errors follow FastAPI's HTTPException format:
```json
{
  "detail": "Error description"
}
```

## Performance Considerations

### Query Optimization
- Use specific filters to reduce data transfer
- Limit results with `top` parameter
- Select only needed columns
- Consider partition key in filters for better performance

### Connection Management
- Uses async context managers for proper cleanup
- Connection pooling handled by Azure SDK
- Automatic retry logic for transient failures

### Scalability
- Stateless design allows horizontal scaling
- Async operations support high concurrency
- Azure Table Storage handles automatic scaling

## Security

### Best Practices
1. **Environment Variables**: Never commit connection strings
2. **Access Control**: Use Azure RBAC for table access
3. **HTTPS**: Always use HTTPS in production
4. **Input Validation**: Pydantic models validate all inputs
5. **Logging**: Avoid logging sensitive data

### Production Deployment
```python
# Use environment variables
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not connection_string:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING not set")
```

## Integration

This server integrates with:
- **MCP-Client**: Receives tool calls via `/mcp` endpoint
- **Azure Table Storage**: Primary data source
- **Monitoring Systems**: Via structured logging
- **Load Balancers**: Stateless design supports scaling

## Troubleshooting

### Common Issues

1. **Azure Connection Errors**
   - Verify connection string format
   - Check Azure Storage account status
   - Ensure table exists

2. **Permission Denied**
   - Verify Azure Storage key
   - Check account access permissions
   - Ensure table access rights

3. **Query Performance**
   - Add partition key to filters
   - Reduce result set with `top`
   - Use selective column queries

4. **Memory Issues**
   - Implement pagination for large datasets
   - Use streaming for bulk operations
   - Monitor memory usage

## Contributing

When modifying MCP-Server:
1. Maintain async/await patterns
2. Follow Pydantic validation standards
3. Update logging for new operations
4. Test with real Azure Table data
5. Document new OData filter examples

---

**Next Steps**: Configure Azure connection string and test the tools with sample table data.