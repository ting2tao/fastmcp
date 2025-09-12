"""
Interactive CLI Client for Native MCP Protocol
Provides a command-line interface to interact with MCP servers
"""
import asyncio
import json
import shlex
import sys
from typing import Any, Dict, List, Tuple

try:
    from .client import MCPClient
    from .protocol import Tool, Resource, Prompt
except ImportError:
    from client import MCPClient
    from protocol import Tool, Resource, Prompt


class MCPInteractiveClient:
    def __init__(self):
        self.client = MCPClient()
        self.connected = False
        self.tools: List[Tool] = []
        self.resources: List[Resource] = []
        self.prompts: List[Prompt] = []
        self.server_info = {}
        
    async def connect(self, host: str = "localhost", port: int = 3000):
        """Connect to MCP server"""
        try:
            await self.client.connect_tcp(host, port)
            init_result = await self.client.initialize("interactive-client", "1.0.0")
            self.server_info = getattr(init_result, "serverInfo", {})
            self.connected = True
            
            # Load available resources
            await self._refresh_capabilities()
            
            print(f"[OK] Connected to {self.server_info.get('name', 'MCP Server')} v{self.server_info.get('version', '1.0.0')}")
            return True
        except Exception as e:
            print(f"[X] Connection failed: {e}")
            return False
    
    async def _refresh_capabilities(self):
        """Refresh the list of available tools, resources, and prompts"""
        try:
            self.tools = await self.client.list_tools()
            self.resources = await self.client.list_resources()
            self.prompts = await self.client.list_prompts()
        except Exception as e:
            print(f"Warning: Could not refresh capabilities: {e}")
    
    def _parse_command(self, command_line: str) -> Tuple[str, List[str], Dict[str, Any]]:
        """Parse command line input into command, args, and kwargs"""
        parts = shlex.split(command_line)
        if not parts:
            return "", [], {}
        
        command = parts[0]
        args = []
        kwargs = {}
        
        i = 1
        while i < len(parts):
            part = parts[i]
            if '=' in part and not part.startswith('-'):
                # Key-value pair
                key, value = part.split('=', 1)
                # Try to parse as JSON, fallback to string
                try:
                    kwargs[key] = json.loads(value)
                except:
                    kwargs[key] = value
            elif part.startswith('--'):
                # Long option
                key = part[2:]
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    i += 1
                    try:
                        kwargs[key] = json.loads(parts[i])
                    except:
                        kwargs[key] = parts[i]
                else:
                    kwargs[key] = True
            else:
                # Positional argument
                try:
                    args.append(json.loads(part))
                except:
                    args.append(part)
            i += 1
        
        return command, args, kwargs
    
    def _format_tool_help(self, tool: Tool) -> str:
        """Format tool help information"""
        help_text = f"Tool: {tool.name}\\n"
        help_text += f"Description: {tool.description}\\n"
        
        if tool.inputSchema and 'properties' in tool.inputSchema:
            help_text += "Parameters:\\n"
            for param, details in tool.inputSchema['properties'].items():
                required = param in tool.inputSchema.get('required', [])
                param_type = details.get('type', 'any')
                param_desc = details.get('description', '')
                help_text += f"  {param} ({param_type}){' [required]' if required else ''}: {param_desc}\\n"
        
        return help_text
    
    def _format_resource_help(self, resource: Resource) -> str:
        """Format resource help information"""
        help_text = f"Resource: {resource.name}\\n"
        help_text += f"URI: {resource.uri}\\n"
        help_text += f"MIME Type: {resource.mimeType or 'unknown'}\\n"
        if resource.description:
            help_text += f"Description: {resource.description}\\n"
        return help_text
    
    def _format_prompt_help(self, prompt: Prompt) -> str:
        """Format prompt help information"""
        help_text = f"Prompt: {prompt.name}\\n"
        help_text += f"Description: {prompt.description}\\n"
        
        if prompt.arguments:
            help_text += "Arguments:\\n"
            for arg in prompt.arguments:
                name = arg.get('name', 'unknown')
                required = arg.get('required', False)
                desc = arg.get('description', '')
                help_text += f"  {name}{' [required]' if required else ''}: {desc}\\n"
        
        return help_text
    
    async def _handle_tool_command(self, args: List[str], kwargs: Dict[str, Any]) -> bool:
        """Handle tool-related commands"""
        if not args:
            # List all tools
            if not self.tools:
                print("No tools available")
                return True
            
            print(f"Available tools ({len(self.tools)}):")
            for tool in self.tools:
                print(f"  {tool.name} - {tool.description}")
            return True
        
        subcommand = args[0]
        
        if subcommand == "help":
            if len(args) < 2:
                print("Usage: tool help <tool_name>")
                return True
            
            tool_name = args[1]
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                print(f"Tool '{tool_name}' not found")
                return True
            
            print(self._format_tool_help(tool))
            return True
        
        elif subcommand == "call":
            if len(args) < 2:
                print("Usage: tool call <tool_name> [param=value ...]")
                return True
            
            tool_name = args[1]
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                print(f"Tool '{tool_name}' not found")
                return True
            
            try:
                result = await self.client.call_tool(tool_name, kwargs)
                print(f"Result from {tool_name}:")
                for content in result.get('content', []):
                    if content.get('type') == 'text':
                        print(content.get('text', ''))
                    else:
                        print(json.dumps(content, indent=2))
            except Exception as e:
                print(f"Error calling tool: {e}")
            return True
        
        elif subcommand == "stream":
            if len(args) < 2:
                print("Usage: tool stream <tool_name> [param=value ...]")
                return True
            
            tool_name = args[1]
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                print(f"Tool '{tool_name}' not found")
                return True
            
            try:
                print(f"Streaming from {tool_name}:")
                async for chunk in self.client.call_tool_streaming(tool_name, kwargs):
                    print(f"  {chunk}")
            except Exception as e:
                print(f"Error streaming from tool: {e}")
            return True
        
        else:
            # Treat as direct tool call
            tool_name = subcommand
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                print(f"Unknown tool command: {subcommand}")
                print("Use 'tool help' for available commands")
                return True
            
            try:
                # Merge remaining args into kwargs if they're key=value pairs
                for arg in args[1:]:
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        try:
                            kwargs[key] = json.loads(value)
                        except:
                            kwargs[key] = value
                
                result = await self.client.call_tool(tool_name, kwargs)
                print(f"Result from {tool_name}:")
                for content in result.get('content', []):
                    if content.get('type') == 'text':
                        print(content.get('text', ''))
                    else:
                        print(json.dumps(content, indent=2))
            except Exception as e:
                print(f"Error calling tool: {e}")
            return True
    
    async def _handle_resource_command(self, args: List[str], kwargs: Dict[str, Any]) -> bool:
        """Handle resource-related commands"""
        if not args:
            # List all resources
            if not self.resources:
                print("No resources available")
                return True
            
            print(f"Available resources ({len(self.resources)}):")
            for resource in self.resources:
                print(f"  {resource.uri} ({resource.name}) - {resource.description or 'No description'}")
            return True
        
        subcommand = args[0]
        
        if subcommand == "help":
            if len(args) < 2:
                print("Usage: resource help <resource_uri>")
                return True
            
            resource_uri = args[1]
            resource = next((r for r in self.resources if r.uri == resource_uri), None)
            if not resource:
                print(f"Resource '{resource_uri}' not found")
                return True
            
            print(self._format_resource_help(resource))
            return True
        
        elif subcommand == "read":
            if len(args) < 2:
                print("Usage: resource read <resource_uri>")
                return True
            
            resource_uri = args[1]
            try:
                content = await self.client.read_resource(resource_uri)
                print(f"Resource: {resource_uri}")
                print(f"MIME Type: {content.mimeType}")
                print("Content:")
                if content.text:
                    print(content.text)
                elif content.blob:
                    print(f"[Binary content, {len(content.blob)} bytes]")
                else:
                    print("[No content]")
            except Exception as e:
                print(f"Error reading resource: {e}")
            return True
        
        else:
            # Treat as direct resource read
            resource_uri = subcommand
            try:
                content = await self.client.read_resource(resource_uri)
                print(f"Resource: {resource_uri}")
                print(f"MIME Type: {content.mimeType}")
                print("Content:")
                if content.text:
                    print(content.text)
                elif content.blob:
                    print(f"[Binary content, {len(content.blob)} bytes]")
                else:
                    print("[No content]")
            except Exception as e:
                print(f"Error reading resource: {e}")
            return True
    
    async def _handle_prompt_command(self, args: List[str], kwargs: Dict[str, Any]) -> bool:
        """Handle prompt-related commands"""
        if not args:
            # List all prompts
            if not self.prompts:
                print("No prompts available")
                return True
            
            print(f"Available prompts ({len(self.prompts)}):")
            for prompt in self.prompts:
                print(f"  {prompt.name} - {prompt.description}")
            return True
        
        subcommand = args[0]
        
        if subcommand == "help":
            if len(args) < 2:
                print("Usage: prompt help <prompt_name>")
                return True
            
            prompt_name = args[1]
            prompt = next((p for p in self.prompts if p.name == prompt_name), None)
            if not prompt:
                print(f"Prompt '{prompt_name}' not found")
                return True
            
            print(self._format_prompt_help(prompt))
            return True
        
        elif subcommand == "get":
            if len(args) < 2:
                print("Usage: prompt get <prompt_name> [arg=value ...]")
                return True
            
            prompt_name = args[1]
            try:
                result = await self.client.get_prompt(prompt_name, kwargs)
                print(f"Prompt: {prompt_name}")
                print("Messages:")
                for message in result.get('messages', []):
                    print(f"  Role: {message.get('role', 'unknown')}")
                    print(f"  Content: {message.get('content', '')}")
                    print()
            except Exception as e:
                print(f"Error getting prompt: {e}")
            return True
        
        else:
            # Treat as direct prompt get
            prompt_name = subcommand
            try:
                result = await self.client.get_prompt(prompt_name, kwargs)
                print(f"Prompt: {prompt_name}")
                print("Messages:")
                for message in result.get('messages', []):
                    print(f"  Role: {message.get('role', 'unknown')}")
                    print(f"  Content: {message.get('content', '')}")
                    print()
            except Exception as e:
                print(f"Error getting prompt: {e}")
            return True
    
    async def _handle_command(self, command_line: str) -> bool:
        """Handle a command line input"""
        command_line = command_line.strip()
        if not command_line:
            return True
        
        command, args, kwargs = self._parse_command(command_line)
        
        if command in ["help", "h", "?"]:
            self._show_help()
            return True
        
        elif command in ["quit", "exit", "q"]:
            return False
        
        elif command == "status":
            await self._show_status()
            return True
        
        elif command == "refresh":
            await self._refresh_capabilities()
            print("Capabilities refreshed")
            return True
        
        elif command == "tool":
            return await self._handle_tool_command(args, kwargs)
        
        elif command == "resource":
            return await self._handle_resource_command(args, kwargs)
        
        elif command == "prompt":
            return await self._handle_prompt_command(args, kwargs)
        
        elif command == "ping":
            try:
                if await self.client.ping():
                    print("[OK] Pong!")
                else:
                    print("[X] No response")
            except Exception as e:
                print(f"[X] Ping failed: {e}")
            return True
        
        else:
            # Check if it's a direct tool name
            tool = next((t for t in self.tools if t.name == command), None)
            if tool:
                try:
                    result = await self.client.call_tool(command, kwargs)
                    print(f"Result from {command}:")
                    for content in result.get('content', []):
                        if content.get('type') == 'text':
                            print(content.get('text', ''))
                        else:
                            print(json.dumps(content, indent=2))
                except Exception as e:
                    print(f"Error calling tool: {e}")
                return True
            
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")
            return True
    
    def _show_help(self):
        """Show help information"""
        print("""
Interactive MCP Client Commands:

Connection:
  status              - Show connection status and server info
  ping                - Ping the server
  refresh             - Refresh available capabilities
  
Tools:
  tool                - List all available tools
  tool help <name>    - Show help for a specific tool
  tool call <name> [args...] - Call a tool with parameters
  tool stream <name> [args...] - Stream from a tool
  <tool_name> [args...] - Direct tool call (shortcut)
  
Resources:
  resource            - List all available resources
  resource help <uri> - Show help for a specific resource
  resource read <uri> - Read a resource
  <resource_uri>      - Direct resource read (if URI format)
  
Prompts:
  prompt              - List all available prompts
  prompt help <name>  - Show help for a specific prompt
  prompt get <name> [args...] - Get a prompt with arguments
  
General:
  help, h, ?          - Show this help
  quit, exit, q       - Exit the client

Parameter format:
  key=value           - String parameter
  key=123             - Number parameter
  key=true            - Boolean parameter
  key='["a","b"]'     - JSON array parameter
  key='{"x":1}'       - JSON object parameter
  
Examples:
  tool call add a=5 b=10
  resource read config://settings
  prompt get greeting name=Alice
  add a=5 b=10        (direct tool call)
""")
    
    async def _show_status(self):
        """Show connection and server status"""
        if not self.connected:
            print("[X] Not connected to server")
            return
        
        print("[OK] Connected to server")
        print(f"Server: {self.server_info.get('name', 'Unknown')} v{self.server_info.get('version', 'Unknown')}")
        print(f"Tools: {len(self.tools)}")
        print(f"Resources: {len(self.resources)}")
        print(f"Prompts: {len(self.prompts)}")
        
        # Test ping
        try:
            if await self.client.ping():
                print("[OK] Server responding to ping")
            else:
                print("[X] Server not responding to ping")
        except:
            print("[X] Ping failed")
    
    async def run_interactive(self):
        """Run the interactive CLI"""
        print("MCP Interactive Client")
        print("=====================")
        print("Type 'help' for available commands, 'quit' to exit")
        print()
        
        while True:
            try:
                command_line = input("mcp> ").strip()
                if not await self._handle_command(command_line):
                    break
            except KeyboardInterrupt:
                print("\\n\\nGoodbye!")
                break
            except EOFError:
                print("\\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        if self.connected:
            await self.client.close()


async def main():
    """Main entry point"""
    client = MCPInteractiveClient()
    
    # Parse command line arguments
    host = "localhost"
    port = 3000
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    print(f"Connecting to MCP server at {host}:{port}...")
    
    if await client.connect(host, port):
        await client.run_interactive()
    else:
        print("Failed to connect. Make sure the MCP server is running.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nExited by user")