"""
Quick test of native MCP implementation with different port
"""
import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from native_mcp import MCPServer, MCPClient


async def test_server_client_communication():
    """Test actual server-client communication"""
    print("Testing server-client communication...")
    
    # Create server with different port
    server = MCPServer("test-server", "1.0.0")
    
    @server.tool("hello", "Say hello")
    def hello_tool(name: str = "World"):
        return f"Hello, {name}!"
    
    # Start server in background
    server_task = asyncio.create_task(server.start_tcp("localhost", 3001))
    
    # Give server time to start
    await asyncio.sleep(0.5)
    
    try:
        # Create and connect client
        client = MCPClient()
        await client.connect_tcp("localhost", 3001)
        
        # Initialize
        init_result = await client.initialize("test-client", "1.0.0")
        print(f"✓ Connected to: {init_result['serverInfo']['name']}")
        
        # List tools
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools: {[t.name for t in tools]}")
        
        # Call tool
        result = await client.call_tool("hello", {"name": "MCP"})
        print(f"✓ Tool call result: {result['content'][0]['text']}")
        
        await client.close()
        print("✓ Client-server communication successful!")
        return True
        
    except Exception as e:
        print(f"✗ Communication error: {e}")
        return False
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


async def main():
    try:
        success = await test_server_client_communication()
        if success:
            print("\n🎉 All communication tests passed!")
        else:
            print("\n❌ Some tests failed")
    except Exception as e:
        print(f"\n❌ Test error: {e}")


if __name__ == "__main__":
    asyncio.run(main())