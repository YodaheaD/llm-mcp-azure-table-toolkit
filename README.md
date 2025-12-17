# LLM Top-Down Architecture Project

## Overview

This project implements a **top-down LLM architecture** that combines Large Language Model inference, Model Context Protocol (MCP) communication, and Azure Table Storage integration. The system is designed as a distributed architecture with three main components working together to provide AI-powered data querying capabilities.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LM-Server     │    │   MCP-Client    │    │   MCP-Server    │
│                 │    │                 │    │                 │
│ • Llama.cpp     │◄──►│ • Tool Calling  │◄──►│ • Azure Tables  │
│ • OpenAI API    │    │ • JSON Parsing  │    │ • Query Engine  │
│ • FastAPI       │    │ • LLM Interface │    │ • FastAPI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 🧠 [LM-Server](./LM-Server/)
Local Language Model server providing OpenAI-compatible API endpoints using Llama.cpp.
- **Purpose**: Text generation and chat completion
- **Technology**: FastAPI + Llama.cpp + GGUF models
- **Features**: Streaming responses, chat completions, temperature control

### 🔗 [MCP-Client](./MCP-Client/)
Middleware client that orchestrates communication between the LLM and external tools.
- **Purpose**: Tool calling coordination and response parsing
- **Technology**: Python + Pydantic + JSON parsing
- **Features**: System prompt management, tool call validation, error handling

### 🗄️ [MCP-Server](./MCP-Server/)
Model Context Protocol server providing Azure Table Storage integration.
- **Purpose**: Data querying and retrieval from Azure Tables
- **Technology**: FastAPI + Azure SDK + Async operations
- **Features**: Entity counting, filtered queries, JSON responses

## Key Features

- **🔄 Distributed Architecture**: Modular design with clear separation of concerns
- **📡 OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **⚡ Streaming Support**: Real-time response streaming with Server-Sent Events
- **🛠️ Tool Integration**: Seamless tool calling via MCP protocol
- **☁️ Cloud Storage**: Azure Table Storage for persistent data
- **🔍 Advanced Querying**: Filtered and paginated data retrieval
- **📝 Type Safety**: Full Pydantic validation and type hints

## Quick Start

### Prerequisites
- Python 3.8+
- Conda environment
- Azure Storage Account (for MCP-Server)
- GGUF model file (for LM-Server)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LLM-Top-Down
   ```

2. **Activate conda environment**
   ```bash
   conda activate llama-http
   ```

3. **Install dependencies for each component**
   ```bash
   # Install LM-Server dependencies
   pip install fastapi llama-cpp-python uvicorn
   
   # Install MCP-Client dependencies
   pip install pydantic requests
   
   # Install MCP-Server dependencies
   pip install fastapi azure-data-tables uvicorn
   ```

### Running the System

1. **Start LM-Server** (Terminal 1)
   ```bash
   cd LM-Server
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start MCP-Server** (Terminal 2)
   ```bash
   cd MCP-Server
   uvicorn app.main:app --reload --port 8001
   ```

3. **Run MCP-Client** (Terminal 3)
   ```bash
   cd MCP-Client
   python client.py
   ```

## Usage Example

Once all services are running, you can ask questions that require data retrieval:

```python
# Example question that triggers tool usage
question = "How many entities are in the Azure table?"

# The system will:
# 1. Send question to LLM-Server
# 2. LLM determines tool needed
# 3. MCP-Client calls MCP-Server
# 4. Returns formatted response
```

## Configuration

- **LM-Server**: Update `MODEL_PATH` in `LM-Server/app/main.py`
- **MCP-Server**: Configure Azure connection string in `MCP-Server/utils/azure_table.py`
- **MCP-Client**: Modify system prompts in `MCP-Client/client.py`

## Development

Each component includes:
- 📁 Detailed component README
- 🧪 Test files and examples
- 📝 Development notes and documentation
- 🔧 Utility functions and helpers

## Contributing

When contributing:
1. Follow the existing code structure
2. Update relevant README files
3. Test all three components together
4. Ensure type hints and validation



---

**Note**: This project demonstrates a practical implementation of distributed LLM architecture with tool calling capabilities. Each component can be developed and deployed independently while maintaining system cohesion.