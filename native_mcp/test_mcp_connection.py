#!/usr/bin/env python3
"""
Simple test to verify MCP streaming works
"""
import asyncio
from client import MCPClient

async def test_mcp_streaming():
    client = MCPClient()
    try:
        print("Connecting to MCP server...")
        await client.connect_tcp("localhost", 3001)
        init_result = await client.initialize("test-client", "1.0.0")
        print(f"Connected: {getattr(init_result, 'serverInfo', {})}")
        
        print("\\nTesting streaming chat...")
        print("User: Hello, tell me about AI")
        print("Assistant: ", end="", flush=True)
        
        async for chunk in client.call_tool_streaming('chat_stream', {
            'message': 'Hello, tell me about AI',
            'response_type': 'helpful'
        }):
            print(chunk + " ", end="", flush=True)
        
        print("\\n\\n✅ MCP streaming works correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_streaming())