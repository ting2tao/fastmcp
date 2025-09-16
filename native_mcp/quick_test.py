#!/usr/bin/env python3
"""
Quick test of streaming chat
"""
import asyncio
from client import MCPClient

async def quick_test():
    client = MCPClient()
    try:
        await client.connect_tcp("localhost", 3001)
        init_result = await client.initialize("test", "1.0.0")
        print(f"Connected to: {getattr(init_result, 'serverInfo', {})}")
        
        print("\\nTesting creative response:")
        async for chunk in client.call_tool_streaming('chat_stream', {
            'message': 'How to be creative?',
            'response_type': 'creative'
        }):
            print(chunk, end=" ", flush=True)
        print("\\n\\nDone!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(quick_test())