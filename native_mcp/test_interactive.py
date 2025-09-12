"""
Test script for the interactive MCP client
Creates a server and tests the interactive client functionality
"""
import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import MCPServer
from interactive_client import MCPInteractiveClient


def create_test_server():
    """Create a test server with various tools and resources"""
    server = MCPServer("test-interactive-server", "1.0.0")
    
    @server.tool("add", "Add two numbers", {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["a", "b"]
    })
    def add_numbers(a: float, b: float):
        return f"The sum of {a} and {b} is {a + b}"
    
    @server.tool("echo", "Echo back a message", {
        "type": "object", 
        "properties": {
            "message": {"type": "string", "description": "Message to echo"},
            "repeat": {"type": "integer", "description": "Number of times to repeat", "default": 1}
        },
        "required": ["message"]
    })
    def echo_message(message: str, repeat: int = 1):
        return "\\n".join([message] * repeat)
    
    @server.tool("countdown", "Count down from a number with streaming")
    async def countdown_stream(start: int = 5):
        for i in range(start, 0, -1):
            yield f"Countdown: {i}"
            await asyncio.sleep(0.5)
        yield "Blast off! 🚀"
    
    @server.resource("info://server", "server-info", "application/json", "Server information")
    def server_info():
        return {
            "name": server.name,
            "version": server.version,
            "tools": list(server.tools.keys()),
            "resources": list(server.resources.keys()),
            "status": "running"
        }
    
    @server.resource("data://sample", "sample-data", "text/plain", "Sample text data")
    def sample_data():
        return "This is sample text data from the test server.\\nIt contains multiple lines.\\nGreat for testing!"
    
    @server.prompt("greeting", "Generate a personalized greeting", [
        {"name": "name", "description": "Person's name", "required": True},
        {"name": "language", "description": "Language for greeting", "required": False}
    ])
    def greeting_prompt(name: str, language: str = "English"):
        greetings = {
            "English": f"Hello, {name}! Welcome to the MCP interactive client.",
            "Spanish": f"¡Hola, {name}! Bienvenido al cliente interactivo MCP.",
            "French": f"Bonjour, {name}! Bienvenue au client interactif MCP.",
            "Chinese": f"你好，{name}！欢迎使用MCP交互式客户端。"
        }
        greeting_text = greetings.get(language, greetings["English"])
        
        return {
            "role": "assistant",
            "content": greeting_text
        }
    
    return server


async def test_client_basic_functionality():
    """Test basic client functionality without server interaction"""
    print("Testing Interactive Client - Basic Functionality")
    print("=" * 50)
    
    client = MCPInteractiveClient()
    
    # Test command parsing
    command, args, kwargs = client._parse_command("tool call add a=5 b=10")
    assert command == "tool"
    assert args == ["call", "add"]
    assert kwargs == {"a": 5, "b": 10}
    print("[OK] Command parsing works")
    
    # Test JSON parameter parsing
    command, args, kwargs = client._parse_command('echo message="Hello World" repeat=3')
    assert command == "echo"
    assert kwargs == {"message": "Hello World", "repeat": 3}
    print("[OK] JSON parameter parsing works")
    
    # Test complex JSON parsing
    command, args, kwargs = client._parse_command('test data=\'{"key": "value", "num": 42}\'')
    assert kwargs["data"] == {"key": "value", "num": 42}
    print("[OK] Complex JSON parsing works")
    
    print("\\nBasic functionality tests passed!")
    return True


async def run_demo_with_server():
    """Run a demo with both server and client"""
    print("\\nStarting Test Server...")
    server = create_test_server()
    
    # Start server in background
    server_task = asyncio.create_task(server.start_tcp("localhost", 3001))
    
    # Give server time to start
    await asyncio.sleep(1)
    
    try:
        print("\\nCreating Interactive Client...")
        client = MCPInteractiveClient()
        
        if await client.connect("localhost", 3001):
            print("\\n" + "=" * 50)
            print("DEMO: Interactive MCP Client")
            print("=" * 50)
            print("Server is running with the following capabilities:")
            print(f"Tools: {[t.name for t in client.tools]}")
            print(f"Resources: {[r.uri for r in client.resources]}")
            print(f"Prompts: {[p.name for p in client.prompts]}")
            
            print("\\nTry these commands:")
            print("  status                    - Show server status")
            print("  tool                      - List tools")
            print("  add a=15 b=27            - Add two numbers")
            print("  echo message='Hi there!' repeat=3")
            print("  tool stream countdown start=5")
            print("  resource read info://server")
            print("  prompt get greeting name=Alice language=Spanish")
            print("  help                      - Show all commands")
            print("  quit                      - Exit")
            
            print("\\nStarting interactive session...")
            print("(Press Ctrl+C to exit)")
            
            await client.run_interactive()
        else:
            print("Failed to connect to test server")
    
    except KeyboardInterrupt:
        print("\\nDemo interrupted")
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("Server stopped")


async def main():
    """Main function"""
    print("MCP Interactive Client Test")
    print("==========================")
    
    # Test basic functionality first
    if not await test_client_basic_functionality():
        print("Basic tests failed!")
        return
    
    # Ask user what they want to do
    print("\\nChoose an option:")
    print("1. Run demo with test server (interactive)")
    print("2. Connect to existing server")
    print("3. Exit")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            await run_demo_with_server()
        elif choice == "2":
            host = input("Server host (default: localhost): ").strip() or "localhost"
            port = input("Server port (default: 3000): ").strip()
            port = int(port) if port else 3000
            
            client = MCPInteractiveClient()
            print(f"Connecting to {host}:{port}...")
            if await client.connect(host, port):
                await client.run_interactive()
            else:
                print("Connection failed!")
        else:
            print("Goodbye!")
    
    except KeyboardInterrupt:
        print("\\nExited by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())