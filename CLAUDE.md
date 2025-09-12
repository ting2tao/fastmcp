# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Commands
- Build: `uv sync` - Install dependencies and sync the environment
- Test: `uv run --frozen pytest -xvs tests` - Run test suite with verbose output
- Test single file: `uv run --frozen pytest -xvs tests/path/to/test_file.py` - Run specific test file
- Typecheck: `uv run pyright` - Run type checking on all files
- Format/Lint: Use `pre-commit run --all-files` (requires `pre-commit install`)

### Alternative Commands via Justfile
- `just build` - Same as `uv sync`  
- `just test` - Same as `uv run --frozen pytest -xvs tests`
- `just typecheck` - Same as `uv run pyright`

### Development Server Commands
- `fastmcp dev your_server.py` - Interactive development with MCP Inspector
- `fastmcp install your_server.py` - Install server for Claude Desktop integration
- `fastmcp install your_server.py --name "Custom Name" --with package1 --env-var KEY=value` - Install with dependencies and env vars
- `uv run python your_server.py` - Direct execution

## Architecture Overview

FastMCP v2 is a Python framework for building MCP (Model Context Protocol) servers and clients. The codebase is organized around four core MCP object types that follow consistent patterns:

### Core MCP Objects (src/fastmcp/)
- **Tools** (`tools/`) - Functions that LLMs can execute to perform actions
- **Resources** (`resources/`) - Static or dynamic data endpoints that provide information  
- **Resource Templates** (`resources/`) - Parameterized resource patterns with URI templates
- **Prompts** (`prompts/`) - Reusable interaction templates for LLMs

Each object type has a corresponding Manager class (ToolManager, ResourceManager, PromptManager) that handles registration, discovery, and protocol interactions.

### Key Components
- **Server** (`server/`) - Core FastMCP server implementation, context handling, proxy functionality
- **Client** (`client/`) - MCP client with multiple transport support (stdio, SSE, WebSocket)
- **Utilities** (`utilities/`) - Shared functionality including decorators, logging, OpenAPI conversion
- **CLI** (`cli/`) - Command-line interface for development and deployment

### Transport Architecture
FastMCP supports multiple transport protocols:
- **PythonStdioTransport** - For local Python scripts via stdin/stdout
- **SSETransport** - Server-Sent Events for web-based servers
- **FastMCPTransport** - Direct in-process connection
- **WSTransport** - WebSocket connections

## Development Patterns

### Testing Structure
Tests mirror the src structure and use pytest with asyncio support. Key test categories:
- Unit tests for individual components
- Integration tests for server-client interactions  
- Transport-specific tests for protocol compliance

### Decorator-Based API
The framework uses decorators extensively:
```python
@mcp.tool()  # Creates MCP tools from functions
@mcp.resource("uri://pattern")  # Creates resources
@mcp.prompt()  # Creates prompt templates
```

### Cursor Rules Integration
When modifying MCP objects, consider impacts across all four core types (Tools, Resources, Resource Templates, Prompts) as they share similar patterns and the ResourceManager handles both resources and templates.

## Project Structure and Key Patterns

### Import Structure
- Main FastMCP entry point: `from fastmcp import FastMCP, Context, Client, Image`
- Core objects available from submodules: `fastmcp.tools`, `fastmcp.resources`, `fastmcp.prompts`, `fastmcp.client`
- Manager classes handle registration and protocol interactions for each object type

### Testing Patterns
- Tests mirror the src structure: `tests/tools/`, `tests/resources/`, `tests/prompts/`, `tests/client/`, `tests/server/`
- Use `pytest` with asyncio support enabled in `pyproject.toml`
- Integration tests in `tests/test_servers/` for full server-client interactions
- Use `conftest.py` for shared test fixtures and configuration

### CLI Structure
- Main CLI entry point: `fastmcp.cli:app` (defined in pyproject.toml)
- Development commands in `src/fastmcp/cli/cli.py`
- Claude Desktop integration in `src/fastmcp/cli/claude.py`
- Environment variable handling supports both command-line args and .env files

### Transport Architecture Details
FastMCP's client-server communication uses pluggable transports:
- **PythonStdioTransport** - Launches Python scripts, communicates via stdin/stdout
- **SSETransport** - HTTP Server-Sent Events for web-based deployments  
- **FastMCPTransport** - Direct in-process connection for testing and composition
- **WSTransport** - WebSocket connections for real-time bidirectional communication

Each transport handles connection lifecycle, message serialization, and error recovery independently.