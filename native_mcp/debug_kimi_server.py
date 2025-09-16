#!/usr/bin/env python3
"""
Debug version of Kimi MCP server to isolate startup issues
"""
import asyncio
import inspect
import json
import os
from typing import Any, Dict, List, Optional, Callable

print("Starting imports...")

try:
    from protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, Prompt,
        ServerCapabilities,
        ErrorCode, MCPError
    )
    print("Protocol imports successful")
except ImportError as e:
    print(f"Protocol import failed: {e}")
    exit(1)

print("Starting server creation...")

async def test_server_creation():
    print("Creating SimplifiedKimiMCPServer...")
    from kimi_demo_server import SimplifiedKimiMCPServer
    
    server = SimplifiedKimiMCPServer("test-server", "1.0.0")
    print("Server object created successfully")
    
    print("Testing server start (without serve_forever)...")
    try:
        # Just test the server creation part
        async_server = await asyncio.start_server(
            server._handle_client, "localhost", 3003
        )
        print("Async server created successfully")
        
        print("Server started - closing for test")
        async_server.close()
        await async_server.wait_closed()
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Server start failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running server creation test...")
    asyncio.run(test_server_creation())
    print("Test finished")