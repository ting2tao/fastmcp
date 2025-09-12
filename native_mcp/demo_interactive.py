"""
Quick demo of the interactive MCP client
Shows key features without requiring user input
"""
import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import MCPServer
from interactive_client import MCPInteractiveClient


async def automated_demo():
    """Run an automated demo showing client capabilities"""
    print("MCP Interactive Client - Automated Demo")
    print("=" * 40)
    
    # Create and start server
    server = MCPServer("demo-server", "1.0.0")
    
    @server.tool("greet", "Greet someone")
    def greet(name: str = "World"):
        return f"Hello, {name}!"
    
    @server.tool("calculate", "Simple calculator")
    def calculate(operation: str, a: float, b: float):
        if operation == "add":
            return f"{a} + {b} = {a + b}"
        elif operation == "multiply":  
            return f"{a} × {b} = {a * b}"
        else:
            return f"Unknown operation: {operation}"
    
    @server.resource("info://demo", "demo-info", "text/plain")
    def demo_info():
        return "This is demo information from the MCP server resource system."
    
    print("Starting server...")
    server_task = asyncio.create_task(server.start_tcp("localhost", 3002))
    await asyncio.sleep(0.5)
    
    try:
        # Create client and connect
        client = MCPInteractiveClient()
        print("Connecting client...")
        
        if await client.connect("localhost", 3002):
            print(f"[OK] Connected to {client.server_info.get('name', 'server')}")
            
            # Demo different commands
            commands_to_test = [
                ("status", "Check server status"),
                ("tool", "List available tools"), 
                ("resource", "List available resources"),
                ("greet name=Alice", "Call greet tool with parameter"),
                ("calculate operation=add a=15 b=27", "Calculate 15 + 27"),
                ("resource read info://demo", "Read demo resource"),
                ("ping", "Test server connectivity")
            ]
            
            print("\\nDemonstrating commands:")
            print("-" * 30)
            
            for command, description in commands_to_test:
                print(f"\\n> {command}")
                print(f"  Description: {description}")
                try:
                    # Simulate the command by calling the handler directly
                    await client._handle_command(command)
                except Exception as e:
                    print(f"  Error: {e}")
                print()
            
            await client.client.close()
            print("Demo completed successfully!")
            
        else:
            print("Failed to connect to server")
    
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


async def show_usage_examples():
    """Show usage examples for the interactive client"""
    print("\\nMCP Interactive Client - Usage Examples")
    print("=" * 40)
    print()
    print("1. Basic Tool Calls:")
    print("   mcp> tool                           # List all tools")
    print("   mcp> tool help add                  # Get help for 'add' tool")
    print("   mcp> tool call add a=5 b=10         # Call tool with parameters")
    print("   mcp> add a=5 b=10                   # Direct tool call (shortcut)")
    print()
    print("2. Streaming Tools:")
    print("   mcp> tool stream countdown start=5  # Stream countdown from 5")
    print()
    print("3. Resources:")
    print("   mcp> resource                       # List all resources")
    print("   mcp> resource read info://server    # Read a specific resource")
    print("   mcp> info://server                  # Direct resource read")
    print()
    print("4. Prompts:")
    print("   mcp> prompt                         # List all prompts")
    print("   mcp> prompt get greeting name=Alice # Get prompt with arguments")
    print()
    print("5. Server Management:")
    print("   mcp> status                         # Show connection status")
    print("   mcp> ping                           # Test server connectivity")
    print("   mcp> refresh                        # Refresh capabilities")
    print()
    print("6. Parameter Formats:")
    print("   mcp> tool call example str='hello' num=42 bool=true")
    print("   mcp> tool call complex data='{\"key\": \"value\", \"count\": 3}'")
    print()
    print("7. Getting Help:")
    print("   mcp> help                           # Show all commands")
    print("   mcp> quit                           # Exit client")


async def main():
    print("Welcome to the MCP Interactive Client!")
    print("=====================================")
    print()
    print("Choose what you'd like to see:")
    print("1. Automated demo (shows functionality)")
    print("2. Usage examples")
    print("3. Start interactive client with demo server")
    print("4. Exit")
    
    try:
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            await automated_demo()
        elif choice == "2":
            await show_usage_examples()
        elif choice == "3":
            # Start demo server and interactive client
            print("\\nStarting demo server and interactive client...")
            print("The server will have tools: greet, calculate")
            print("And resource: info://demo")
            print("\\nPress Ctrl+C to exit when done.")
            
            # This would start the full interactive experience
            from test_interactive import run_demo_with_server
            await run_demo_with_server()
        else:
            print("Goodbye!")
    
    except KeyboardInterrupt:
        print("\\nExited by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())