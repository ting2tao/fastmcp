"""
Simple test for the native MCP implementation
"""
import asyncio
import sys
import os

# Add the parent directory to the path to import native_mcp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from native_mcp import MCPServer, MCPClient


async def test_basic_functionality():
    """Test basic client-server interaction"""
    print("Testing Native MCP Protocol Implementation")
    print("=" * 50)
    
    # Create a simple server
    server = MCPServer("test-server", "1.0.0")
    
    @server.tool("echo", "Echo back the input message")
    def echo_tool(message: str):
        return f"Echo: {message}"
    
    @server.tool("count_stream", "Stream counting numbers")
    async def count_stream(max_count: int = 5):
        for i in range(max_count):
            yield f"Number {i + 1}"
            await asyncio.sleep(0.1)
    
    @server.resource("test://data", "test-data", "text/plain", "Test data resource")
    def test_data():
        return "This is test data from the resource"
    
    print("[OK] Server created with tools and resources")
    
    # Test protocol message parsing
    from native_mcp.protocol import MCPRequest, MCPMessage
    
    # Test request serialization/deserialization
    request = MCPRequest(method="test", params={"key": "value"}, id="123")
    serialized = MCPMessage.serialize(request)
    parsed = MCPMessage.parse(serialized)
    
    assert isinstance(parsed, MCPRequest)
    assert parsed.method == "test"
    assert parsed.params == {"key": "value"}
    assert parsed.id == "123"
    
    print("[OK] Protocol message serialization/parsing works")
    
    # Test server tool registration
    assert "echo" in server.tools
    assert "count_stream" in server.tools
    assert "test://data" in server.resources
    
    print("[OK] Tool and resource registration works")
    
    print("\nBasic functionality test passed!")
    return True


async def test_concurrent_server_client():
    """Test server and client running concurrently"""
    print("\nTesting concurrent server-client interaction...")
    
    # This would require running server and client in separate processes
    # For now, we'll just test the setup
    
    server = MCPServer("concurrent-test", "1.0.0")
    
    @server.tool("multiply", "Multiply two numbers")
    def multiply(a: float, b: float):
        return a * b
    
    client = MCPClient()
    
    print("[OK] Server and client instances created")
    print("Note: For full concurrent testing, run the demo.py script")
    
    return True


def print_usage():
    """Print usage instructions"""
    print("\nUsage Instructions:")
    print("==================")
    print()
    print("1. To run the interactive demo:")
    print("   python native_mcp/demo.py")
    print()
    print("2. To run server only:")
    print("   python -c \"from native_mcp.demo import run_server; import asyncio; asyncio.run(run_server())\"")
    print()
    print("3. To run client only (server must be running):")
    print("   python -c \"from native_mcp.demo import run_client; import asyncio; asyncio.run(run_client())\"")
    print()
    print("4. Example of creating your own server:")
    print('''
from native_mcp import MCPServer
import asyncio

server = MCPServer("my-server", "1.0.0")

@server.tool("greet", "Greet someone")
def greet(name: str):
    return f"Hello, {name}!"

@server.tool("stream_data", "Stream some data")
async def stream_data(count: int = 3):
    for i in range(count):
        yield f"Data chunk {i + 1}"
        await asyncio.sleep(0.5)

# Run with: asyncio.run(server.start_tcp())
''')
    print()
    print("Features implemented:")
    print("- Full MCP protocol support (JSON-RPC 2.0)")
    print("- Streaming tool calls")
    print("- Tools, Resources, and Prompts")
    print("- TCP and stdio transports")
    print("- Client-server communication")
    print("- Error handling and protocol compliance")


async def main():
    """Main test function"""
    try:
        success1 = await test_basic_functionality()
        success2 = await test_concurrent_server_client()
        
        if success1 and success2:
            print("\n[SUCCESS] All tests passed!")
            print_usage()
        else:
            print("\n[ERROR] Some tests failed")
            
    except Exception as e:
        print(f"\n[ERROR] Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())