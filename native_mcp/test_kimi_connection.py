#!/usr/bin/env python3
"""
Simple test script to test direct connection to Kimi MCP server
"""
import asyncio
import sys

try:
    from client import MCPClient
except ImportError:
    sys.path.append('.')
    from client import MCPClient

async def test_kimi_mcp_connection():
    """Test direct connection to Kimi MCP server"""
    client = None
    try:
        print("[TEST] Creating MCP client...")
        client = MCPClient()
        
        print("[TEST] Connecting to localhost:3002...")
        await client.connect_tcp("localhost", 3002)
        
        print("[TEST] Initializing client...")
        init_result = await client.initialize("test-client", "1.0.0")
        print(f"[TEST] Server info: {getattr(init_result, 'serverInfo', {})}")
        
        print("[TEST] Testing ping...")
        ping_result = await client.ping()
        print(f"[TEST] Ping result: {ping_result}")
        
        print("[TEST] Listing tools...")
        tools = await client.list_tools()
        print(f"[TEST] Available tools: {[tool.get('name', 'unknown') for tool in tools.get('tools', [])]}")
        
        print("[TEST] Testing kimi_models tool...")
        models_result = await client.call_tool("kimi_models", {})
        print(f"[TEST] Models result: {models_result}")
        
        print("[TEST] All tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client:
            try:
                await client.close()
                print("[TEST] Client closed")
            except:
                pass

if __name__ == "__main__":
    print("Testing Kimi MCP Server Connection...")
    result = asyncio.run(test_kimi_mcp_connection())
    sys.exit(0 if result else 1)