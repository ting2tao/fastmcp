"""
Example: MCP Client-Server Interaction Demo
This demonstrates the native MCP protocol implementation with streaming support
"""
import asyncio
import sys
import os
from typing import AsyncIterator

# Add the native_mcp directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from native_mcp.server import MCPServer
from native_mcp.client import MCPClient


def create_demo_server():
    """Create a demo server with various tools and resources"""
    server = MCPServer("demo-server", "1.0.0")
    
    @server.tool("add", "Add two numbers", {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["a", "b"]
    })
    def add_numbers(a: float, b: float):
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    @server.tool("fibonacci", "Generate Fibonacci sequence with streaming output")
    async def fibonacci_stream(count: int = 10) -> AsyncIterator[str]:
        """Generate Fibonacci numbers with streaming output"""
        a, b = 0, 1
        for i in range(count):
            yield f"Fibonacci {i+1}: {a}"
            a, b = b, a + b
            await asyncio.sleep(0.2)  # Simulate processing time
    
    @server.tool("weather", "Get weather information", {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "country": {"type": "string", "description": "Country code"}
        },
        "required": ["city"]
    })
    def get_weather(city: str, country: str = "US"):
        # Mock weather data
        return f"Weather in {city}, {country}: Sunny, 25°C"
    
    @server.resource("info://server", "server-info", "application/json", "Server information")
    def server_info():
        return {
            "name": "Demo MCP Server",
            "version": "1.0.0",
            "protocol_version": "2024-11-05",
            "features": ["tools", "resources", "prompts", "streaming"],
            "tools_count": len(server.tools),
            "resources_count": len(server.resources)
        }
    
    @server.resource("data://sample", "sample-data", "text/plain", "Sample text data")
    def sample_data():
        return "This is sample text data from the MCP server resource."
    
    @server.prompt("task_planner", "Generate a task planning prompt", [
        {"name": "task_type", "description": "Type of task to plan", "required": True},
        {"name": "complexity", "description": "Task complexity level", "required": False}
    ])
    def task_planner_prompt(task_type: str, complexity: str = "medium"):
        return {
            "role": "system", 
            "content": f"Plan a {complexity} complexity {task_type} task. Break it down into steps and provide clear instructions."
        }
    
    return server


async def run_server():
    """Run the demo server"""
    server = create_demo_server()
    print("Starting MCP Demo Server on localhost:3000...")
    print("Available tools:", list(server.tools.keys()))
    print("Available resources:", list(server.resources.keys()))
    print("Available prompts:", list(server.prompts.keys()))
    print()
    
    try:
        await server.start_tcp("localhost", 3000)
    except KeyboardInterrupt:
        print("\\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        await server.stop()


async def run_client():
    """Run the demo client"""
    client = MCPClient()
    
    try:
        print("Connecting to MCP Demo Server...")
        await client.connect_tcp("localhost", 3000)
        
        # Initialize connection
        init_result = await client.initialize("demo-client", "1.0.0")
        print(f"✓ Connected to: {init_result.serverInfo['name']} v{init_result.serverInfo['version']}")
        print()
        
        # Test ping
        if await client.ping():
            print("✓ Server ping successful")
        
        # List and demonstrate tools
        print("\\n=== TOOLS DEMO ===")
        tools = await client.list_tools()
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test regular tool call
        print("\\n--- Regular Tool Call ---")
        if any(tool.name == "add" for tool in tools):
            result = await client.call_tool("add", {"a": 15, "b": 27})
            print(f"add(15, 27) = {result['content'][0]['text']}")
        
        # Test weather tool
        if any(tool.name == "weather" for tool in tools):
            result = await client.call_tool("weather", {"city": "Beijing", "country": "CN"})
            print(f"Weather result: {result['content'][0]['text']}")
        
        # Test streaming tool call
        print("\\n--- Streaming Tool Call ---")
        if any(tool.name == "fibonacci" for tool in tools):
            print("Fibonacci sequence (streaming):")
            try:
                async for chunk in client.call_tool_streaming("fibonacci", {"count": 8}):
                    print(f"  {chunk}")
            except Exception as e:
                print(f"  Streaming error (expected in demo): {e}")
        
        # Test resources
        print("\\n=== RESOURCES DEMO ===")
        resources = await client.list_resources()
        print(f"Available resources ({len(resources)}):")
        for resource in resources:
            print(f"  - {resource.uri}: {resource.name} ({resource.mimeType})")
        
        # Read resources
        for resource in resources:
            content = await client.read_resource(resource.uri)
            print(f"\\n--- Resource: {resource.uri} ---")
            if content.text:
                print(content.text[:200] + "..." if len(content.text) > 200 else content.text)
        
        # Test prompts
        print("\\n=== PROMPTS DEMO ===")
        prompts = await client.list_prompts()
        print(f"Available prompts ({len(prompts)}):")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        
        # Get a prompt
        if prompts:
            prompt_result = await client.get_prompt("task_planner", {
                "task_type": "software development",
                "complexity": "high"
            })
            print(f"\\n--- Prompt Result ---")
            for message in prompt_result['messages']:
                print(f"Role: {message['role']}")
                print(f"Content: {message['content']}")
        
        print("\\n✓ Demo completed successfully!")
        
    except Exception as e:
        print(f"Client error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


async def interactive_demo():
    """Interactive demonstration"""
    print("MCP Native Protocol Demo")
    print("========================")
    print()
    
    choice = input("Choose mode:\\n1. Run Server\\n2. Run Client\\n3. Full Demo (both)\\nEnter choice (1-3): ")
    
    if choice == "1":
        await run_server()
    elif choice == "2":
        await run_client()
    elif choice == "3":
        print("Starting server and client demo...")
        print("\\nNote: Start server first, then run client in another terminal")
        print("Server will run until you press Ctrl+C")
        await run_server()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        asyncio.run(interactive_demo())
    except KeyboardInterrupt:
        print("\\nDemo interrupted by user")