#!/usr/bin/env python3
"""
Test script for streaming tool functionality
"""
import asyncio
import sys

try:
    from client import MCPClient
except ImportError:
    sys.path.append('.')
    from client import MCPClient


async def test_streaming_tool():
    """Test the streaming tool functionality"""
    client = MCPClient()
    
    try:
        # Connect to server
        print("Connecting to server...")
        await client.connect_tcp("localhost", 3001)
        
        # Initialize
        print("Initializing...")
        init_result = await client.initialize("test-client", "1.0.0")
        print(f"Connected to: {getattr(init_result, 'serverInfo', {})}")
        
        # List tools
        print("\nListing tools...")
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test regular tool call
        print("\nTesting regular tool call...")
        result = await client.call_tool("calculate", {"expression": "2+2"})
        print(f"Regular tool result: {result}")
        
        # Test streaming tool call
        print("\nTesting streaming tool call...")
        result = await client.call_tool("streaming_count", {"max_count": 3})
        print(f"Streaming tool result: {result}")
        
        # Test actual streaming
        print("\nTesting actual streaming...")
        async for chunk in client.call_tool_streaming("streaming_count", {"max_count": 3}):
            print(f"Streaming chunk: {chunk}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_streaming_tool())