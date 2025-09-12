"""
Native MCP Server Implementation with Streaming Support
"""
import asyncio
import inspect
from typing import Any, Dict, List, Optional, Callable

try:
    from .protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, Prompt,
        ServerCapabilities,
        ErrorCode, MCPError
    )
except ImportError:
    from protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, Prompt,
        ServerCapabilities,
        ErrorCode, MCPError
    )


class MCPServer:
    def __init__(self, name: str = "native-mcp-server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = False
        
    def tool(self, name: Optional[str] = None, description: str = "", input_schema: Optional[Dict[str, Any]] = None):
        """Decorator to register a tool"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            
            # Store metadata
            func._mcp_name = tool_name
            func._mcp_description = description
            func._mcp_input_schema = input_schema or self._generate_input_schema(func)
            return func
        return decorator
        
    def resource(self, uri: str, name: Optional[str] = None, mime_type: str = "text/plain", description: str = ""):
        """Decorator to register a resource"""
        def decorator(func: Callable):
            resource_name = name or func.__name__
            self.resources[uri] = func
            
            func._mcp_uri = uri
            func._mcp_name = resource_name
            func._mcp_mime_type = mime_type
            func._mcp_description = description
            return func
        return decorator
        
    def prompt(self, name: Optional[str] = None, description: str = "", arguments: Optional[List[Dict[str, Any]]] = None):
        """Decorator to register a prompt"""
        def decorator(func: Callable):
            prompt_name = name or func.__name__
            self.prompts[prompt_name] = func
            
            func._mcp_name = prompt_name
            func._mcp_description = description
            func._mcp_arguments = arguments or []
            return func
        return decorator
        
    def _generate_input_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate JSON schema from function signature"""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
                    
            properties[param_name] = {"type": param_type}
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
    async def start_stdio(self):
        """Start server using stdio transport"""
        import sys
        
        self.reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self.reader)
        transport, _ = await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin
        )
        
        self.writer = asyncio.StreamWriter(
            transport=sys.stdout,
            protocol=None,
            reader=None,
            loop=asyncio.get_event_loop()
        )
        
        self.running = True
        await self._message_loop()
        
    async def start_tcp(self, host: str = "localhost", port: int = 3000):
        """Start server using TCP transport"""
        server = await asyncio.start_server(
            self._handle_client, host, port
        )
        
        print(f"MCP Server running on {host}:{port}")
        self.running = True
        
        async with server:
            await server.serve_forever()
            
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection"""
        self.reader = reader
        self.writer = writer
        
        try:
            await self._message_loop()
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def _message_loop(self):
        """Main message processing loop"""
        while self.running and self.reader:
            try:
                line = await self.reader.readline()
                if not line:
                    break
                    
                message_str = line.decode().strip()
                if not message_str:
                    continue
                    
                await self._handle_message(message_str)
                    
            except Exception as e:
                print(f"Error in message loop: {e}")
                break
                
    async def _handle_message(self, message_str: str):
        """Handle incoming messages"""
        try:
            message = MCPMessage.parse(message_str)
            
            if isinstance(message, MCPRequest):
                await self._handle_request(message)
            elif isinstance(message, MCPNotification):
                await self._handle_notification(message)
                
        except Exception as e:
            print(f"Error handling message: {e}")
            
    async def _handle_request(self, request: MCPRequest):
        """Handle RPC requests"""
        try:
            if request.method == "initialize":
                result = await self._handle_initialize(request.params or {})
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "tools/list":
                result = await self._handle_tools_list()
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "tools/call":
                result = await self._handle_tool_call(request)
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "resources/list":
                result = await self._handle_resources_list()
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "resources/read":
                result = await self._handle_resource_read(request.params or {})
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "prompts/list":
                result = await self._handle_prompts_list()
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "prompts/get":
                result = await self._handle_prompt_get(request.params or {})
                response = MCPResponse(id=request.id, result=result)
                
            elif request.method == "ping":
                response = MCPResponse(id=request.id, result={})
                
            else:
                error = MCPError(ErrorCode.METHOD_NOT_FOUND, f"Method not found: {request.method}")
                response = MCPResponse(id=request.id, error=error)
                
            await self._send_response(response)
            
        except Exception as e:
            error = MCPError(ErrorCode.INTERNAL_ERROR, str(e))
            response = MCPResponse(id=request.id, error=error)
            await self._send_response(response)
            
    async def _handle_notification(self, notification: MCPNotification):
        """Handle notifications"""
        if notification.method == "initialized":
            print("Client initialized")
        elif notification.method == "cancelled":
            print("Request cancelled")
            
    async def _send_response(self, response: MCPResponse):
        """Send a response"""
        if not self.writer:
            return
            
        message_str = MCPMessage.serialize(response) + "\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification"""
        if not self.writer:
            return
            
        notification = MCPNotification(method=method, params=params)
        message_str = MCPMessage.serialize(notification) + "\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True} if self.tools else None,
                "resources": {"subscribe": True, "listChanged": True} if self.resources else None,
                "prompts": {"listChanged": True} if self.prompts else None,
                "experimental": {"streaming": True}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
        
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = []
        for tool_name, func in self.tools.items():
            tool = Tool(
                name=getattr(func, '_mcp_name', tool_name),
                description=getattr(func, '_mcp_description', ''),
                inputSchema=getattr(func, '_mcp_input_schema', {})
            )
            tools.append(tool.__dict__)
            
        return {"tools": tools}
        
    async def _handle_tool_call(self, request: MCPRequest) -> Any:
        """Handle tools/call request"""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
            
        func = self.tools[tool_name]
        
        # Check if function returns an async iterator (streaming)
        if inspect.isasyncgenfunction(func):
            # Handle streaming response
            result_chunks = []
            async for chunk in func(**arguments):
                # Send streaming notification
                await self._send_notification("tools/stream", {
                    "id": request.id,
                    "data": chunk
                })
                result_chunks.append(chunk)
                
            # Send completion notification
            await self._send_notification("tools/stream", {
                "id": request.id,
                "done": True
            })
            
            return {"content": [{"type": "text", "text": chunk} for chunk in result_chunks]}
        else:
            # Regular tool call
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)
                
            return {"content": [{"type": "text", "text": str(result)}]}
            
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = []
        for uri, func in self.resources.items():
            resource = Resource(
                uri=getattr(func, '_mcp_uri', uri),
                name=getattr(func, '_mcp_name', func.__name__),
                mimeType=getattr(func, '_mcp_mime_type', 'text/plain'),
                description=getattr(func, '_mcp_description', '')
            )
            resources.append(resource.__dict__)
            
        return {"resources": resources}
        
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
            
        func = self.resources[uri]
        
        if inspect.iscoroutinefunction(func):
            content = await func()
        else:
            content = func()
            
        return {
            "contents": [{
                "uri": uri,
                "mimeType": getattr(func, '_mcp_mime_type', 'text/plain'),
                "text": str(content)
            }]
        }
        
    async def _handle_prompts_list(self) -> Dict[str, Any]:
        """Handle prompts/list request"""
        prompts = []
        for prompt_name, func in self.prompts.items():
            prompt = Prompt(
                name=getattr(func, '_mcp_name', prompt_name),
                description=getattr(func, '_mcp_description', ''),
                arguments=getattr(func, '_mcp_arguments', [])
            )
            prompts.append(prompt.__dict__)
            
        return {"prompts": prompts}
        
    async def _handle_prompt_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_name}")
            
        func = self.prompts[prompt_name]
        
        if inspect.iscoroutinefunction(func):
            result = await func(**arguments)
        else:
            result = func(**arguments)
            
        return {"messages": result if isinstance(result, list) else [result]}
        
    async def stop(self):
        """Stop the server"""
        self.running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()


# Example usage
def create_example_server():
    server = MCPServer("example-server", "1.0.0")
    
    @server.tool("calculate", "Perform mathematical calculations", {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
        },
        "required": ["expression"]
    })
    def calculate(expression: str):
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
            
    @server.tool("streaming_count", "Count with streaming output")
    async def streaming_count(max_count: int = 5):
        for i in range(max_count):
            yield f"Count: {i + 1}"
            await asyncio.sleep(0.5)
            
    @server.resource("config://settings", "settings", "application/json", "Server configuration")
    def get_settings():
        return {
            "name": server.name,
            "version": server.version,
            "capabilities": ["tools", "resources", "prompts", "streaming"]
        }
        
    @server.prompt("greeting", "Generate a greeting message")
    def greeting_prompt(name: str = "User"):
        return {
            "role": "user",
            "content": f"Generate a friendly greeting for {name}"
        }
        
    return server


async def run_example_server():
    server = create_example_server()
    
    try:
        # Start TCP server on port 3001
        await server.start_tcp(port=3001)
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(run_example_server())