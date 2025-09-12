"""
Native MCP Client Implementation with Streaming Support
"""
import asyncio
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator, Callable

try:
    from .protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, ResourceContent, Prompt,
        InitializeParams, InitializeResult, ClientCapabilities
    )
except ImportError:
    from protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, ResourceContent, Prompt,
        InitializeParams, InitializeResult, ClientCapabilities
    )


class MCPClient:
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.connected = False
        self.capabilities: Optional[Dict[str, Any]] = None
        
    async def connect_stdio(self):
        """Connect using stdio transport"""
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
        
        self.connected = True
        asyncio.create_task(self._message_loop())
        
    async def connect_tcp(self, host: str = "localhost", port: int = 3000):
        """Connect using TCP transport"""
        self.reader, self.writer = await asyncio.open_connection(host, port)
        self.connected = True
        asyncio.create_task(self._message_loop())
        
    async def _message_loop(self):
        """Main message processing loop"""
        while self.connected and self.reader:
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
            
            if isinstance(message, MCPResponse):
                request_id = str(message.id)
                if request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if message.error:
                        future.set_exception(Exception(f"MCP Error: {message.error.message}"))
                    else:
                        future.set_result(message.result)
                        
            elif isinstance(message, MCPNotification):
                handler = self.notification_handlers.get(message.method)
                if handler:
                    await handler(message.params or {})
                    
        except Exception as e:
            print(f"Error handling message: {e}")
            
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a request and wait for response"""
        if not self.connected or not self.writer:
            raise RuntimeError("Client not connected")
            
        request_id = str(uuid.uuid4())
        request = MCPRequest(method=method, params=params, id=request_id)
        
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        message_str = MCPMessage.serialize(request) + "\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
        return await future
        
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification (no response expected)"""
        if not self.connected or not self.writer:
            raise RuntimeError("Client not connected")
            
        notification = MCPNotification(method=method, params=params)
        message_str = MCPMessage.serialize(notification) + "\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
    def add_notification_handler(self, method: str, handler: Callable):
        """Add a handler for notifications"""
        self.notification_handlers[method] = handler
        
    async def initialize(self, client_name: str = "native-mcp-client", client_version: str = "1.0.0"):
        """Initialize the MCP connection"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "experimental": {"streaming": True}
            },
            "clientInfo": {
                "name": client_name,
                "version": client_version
            }
        }
        
        result = await self._send_request("initialize", params)
        self.capabilities = result.get("capabilities", {})
        
        await self._send_notification("initialized")
        return InitializeResult(**result)
        
    async def list_tools(self) -> List[Tool]:
        """List available tools"""
        result = await self._send_request("tools/list")
        return [Tool(**tool) for tool in result.get("tools", [])]
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool"""
        params = {
            "name": name,
            "arguments": arguments
        }
        return await self._send_request("tools/call", params)
        
    async def call_tool_streaming(self, name: str, arguments: Dict[str, Any]) -> AsyncIterator[Any]:
        """Call a tool with streaming response"""
        params = {
            "name": name,
            "arguments": arguments
        }
        
        request_id = str(uuid.uuid4())
        request = MCPRequest(method="tools/call", params=params, id=request_id)
        
        stream_queue = asyncio.Queue()
        
        async def stream_handler(notification_params: Dict[str, Any]):
            if notification_params.get("id") == request_id:
                if "data" in notification_params:
                    await stream_queue.put(notification_params["data"])
                elif "done" in notification_params:
                    await stream_queue.put(None)  # End marker
                    
        self.add_notification_handler("tools/stream", stream_handler)
        
        message_str = MCPMessage.serialize(request) + "\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
        while True:
            data = await stream_queue.get()
            if data is None:
                break
            yield data
            
    async def list_resources(self) -> List[Resource]:
        """List available resources"""
        result = await self._send_request("resources/list")
        return [Resource(**resource) for resource in result.get("resources", [])]
        
    async def read_resource(self, uri: str) -> ResourceContent:
        """Read a resource"""
        params = {"uri": uri}
        result = await self._send_request("resources/read", params)
        return ResourceContent(**result["contents"][0])
        
    async def list_prompts(self) -> List[Prompt]:
        """List available prompts"""
        result = await self._send_request("prompts/list")
        return [Prompt(**prompt) for prompt in result.get("prompts", [])]
        
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Get a prompt"""
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send_request("prompts/get", params)
        
    async def ping(self) -> bool:
        """Ping the server"""
        try:
            await self._send_request("ping")
            return True
        except:
            return False
            
    async def close(self):
        """Close the connection"""
        self.connected = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()


# Example usage
async def example_client():
    client = MCPClient()
    
    try:
        # Connect to server
        await client.connect_tcp()
        
        # Initialize
        init_result = await client.initialize("example-client", "1.0.0")
        print(f"Connected to server: {init_result.serverInfo}")
        
        # List and call tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Example streaming tool call
        if tools:
            async for chunk in client.call_tool_streaming(tools[0].name, {}):
                print(f"Streaming chunk: {chunk}")
                
        # List resources
        resources = await client.list_resources()
        print(f"Available resources: {[resource.uri for resource in resources]}")
        
    finally:
        await client.close()
        

if __name__ == "__main__":
    import sys
    asyncio.run(example_client())