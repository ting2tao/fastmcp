#!/usr/bin/env python3
"""
Robust MCP Client with better connection handling
"""
import asyncio
import uuid
import traceback
from typing import Any, Dict, List, Optional, AsyncIterator, Callable

try:
    from protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, ResourceContent, Prompt,
        InitializeParams, InitializeResult, ClientCapabilities
    )
except ImportError:
    from .protocol import (
        MCPRequest, MCPResponse, MCPNotification, MCPMessage,
        Tool, Resource, ResourceContent, Prompt,
        InitializeParams, InitializeResult, ClientCapabilities
    )


class RobustMCPClient:
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.connected = False
        self.capabilities: Optional[Dict[str, Any]] = None
        self._connection_lock = asyncio.Lock()
        
    async def connect_tcp(self, host: str = "localhost", port: int = 3001):
        """Connect using TCP transport with robust error handling"""
        async with self._connection_lock:
            try:
                # Close existing connection if any
                if self.writer and not self.writer.is_closing():
                    self.writer.close()
                    await self.writer.wait_closed()
                
                # Reset state
                self.reader = None
                self.writer = None
                self.connected = False
                self.pending_requests.clear()
                
                # Establish new connection
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=5.0
                )
                
                self.connected = True
                
                # Start message loop
                asyncio.create_task(self._message_loop())
                
                print(f"[DEBUG] Connected to {host}:{port}")
                
            except Exception as e:
                print(f"[ERROR] Connection failed: {e}")
                self.connected = False
                self.reader = None
                self.writer = None
                raise
    
    def is_connected(self) -> bool:
        """Check if client is properly connected"""
        return (
            self.connected and 
            self.writer is not None and 
            not self.writer.is_closing() and
            self.reader is not None
        )
        
    async def _message_loop(self):
        """Main message processing loop with error handling"""
        try:
            while self.is_connected():
                try:
                    line = await asyncio.wait_for(self.reader.readline(), timeout=1.0)
                    if not line:
                        print("[WARN] Empty line received, connection may be closed")
                        break
                        
                    message_str = line.decode().strip()
                    if not message_str:
                        continue
                        
                    await self._handle_message(message_str)
                        
                except asyncio.TimeoutError:
                    # Check if connection is still alive
                    if not self.is_connected():
                        break
                    continue
                except Exception as e:
                    print(f"[ERROR] Message loop error: {e}")
                    break
                    
        except Exception as e:
            print(f"[ERROR] Message loop fatal error: {e}")
        finally:
            print("[DEBUG] Message loop ended")
            self.connected = False
                
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
            print(f"[ERROR] Handle message error: {e}")
            
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a request and wait for response with robust error handling"""
        if not self.is_connected():
            raise RuntimeError("Client not connected or connection is invalid")
            
        request_id = str(uuid.uuid4())
        request = MCPRequest(method=method, params=params, id=request_id)
        
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            message_str = MCPMessage.serialize(request) + "\\n"
            self.writer.write(message_str.encode())
            await self.writer.drain()
            
            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout=10.0)
            
        except asyncio.TimeoutError:
            # Clean up pending request
            self.pending_requests.pop(request_id, None)
            raise RuntimeError(f"Request timeout for method: {method}")
        except Exception as e:
            # Clean up pending request
            self.pending_requests.pop(request_id, None)
            print(f"[ERROR] Send request error: {e}")
            raise RuntimeError(f"Send request failed: {str(e)}")
        
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification (no response expected)"""
        if not self.is_connected():
            raise RuntimeError("Client not connected")
            
        try:
            notification = MCPNotification(method=method, params=params)
            message_str = MCPMessage.serialize(notification) + "\\n"
            self.writer.write(message_str.encode())
            await self.writer.drain()
        except Exception as e:
            print(f"[ERROR] Send notification error: {e}")
            raise RuntimeError(f"Send notification failed: {str(e)}")
        
    def add_notification_handler(self, method: str, handler: Callable):
        """Add a handler for notifications"""
        self.notification_handlers[method] = handler
        
    async def initialize(self, client_name: str = "robust-mcp-client", client_version: str = "1.0.0"):
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
        stream_done = asyncio.Event()
        
        async def stream_handler(notification_params: Dict[str, Any]):
            if notification_params.get("id") == request_id:
                if "data" in notification_params:
                    await stream_queue.put(notification_params["data"])
                elif "done" in notification_params:
                    stream_done.set()
                    
        self.add_notification_handler("tools/stream", stream_handler)
        
        try:
            message_str = MCPMessage.serialize(request) + "\\n"
            self.writer.write(message_str.encode())
            await self.writer.drain()
            
            # Yield data as it comes
            while not stream_done.is_set():
                try:
                    data = await asyncio.wait_for(stream_queue.get(), timeout=1.0)
                    yield data
                except asyncio.TimeoutError:
                    if not self.is_connected():
                        break
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Streaming tool call error: {e}")
            raise RuntimeError(f"Streaming failed: {str(e)}")
            
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
        if self.writer and not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None
        self.pending_requests.clear()


# For backward compatibility, use the robust client
MCPClient = RobustMCPClient