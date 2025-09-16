#!/usr/bin/env python3
"""
MCP Streaming Chat Web Server
Provides HTTP endpoints for web UI to connect to MCP server
"""
import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any, Optional
from aiohttp import web, WebSocketResponse, WSMsgType
import aiohttp_cors

try:
    from client import MCPClient
except ImportError:
    import sys
    sys.path.append('.')
    from client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPWebServer:
    def __init__(self, mcp_host: str = "localhost", mcp_port: int = 3001):
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.mcp_client: Optional[MCPClient] = None
        self.websocket_connections = set()
        
    async def connect_to_mcp(self) -> bool:
        """Connect to MCP server"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
                
            self.mcp_client = MCPClient()
            await self.mcp_client.connect_tcp(self.mcp_host, self.mcp_port)
            init_result = await self.mcp_client.initialize("web-chat-client", "1.0.0")
            logger.info(f"Connected to MCP server: {getattr(init_result, 'serverInfo', {})}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.mcp_client = None
            return False
    
    async def handle_index(self, request):
        """Serve the chat interface HTML"""
        try:
            with open('chat_interface.html', 'r', encoding='utf-8') as f:
                content = f.read()
            return web.Response(text=content, content_type='text/html')
        except FileNotFoundError:
            return web.Response(text="Chat interface not found", status=404)
    
    async def handle_connect(self, request):
        """Handle MCP connection request"""
        success = await self.connect_to_mcp()
        return web.json_response({
            'success': success,
            'message': 'Connected to MCP server' if success else 'Failed to connect to MCP server'
        })
    
    async def handle_tools(self, request):
        """List available MCP tools"""
        if not self.mcp_client:
            return web.json_response({'error': 'Not connected to MCP server'}, status=400)
        
        try:
            tools = await self.mcp_client.list_tools()
            return web.json_response({
                'tools': [{'name': tool.name, 'description': tool.description} for tool in tools]
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections for real-time streaming"""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.add(ws)
        logger.info(f"WebSocket connected. Total connections: {len(self.websocket_connections)}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON format'
                        }))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.websocket_connections)}")
        
        return ws
    
    async def handle_websocket_message(self, ws: WebSocketResponse, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        message_type = data.get('type')
        
        if message_type == 'connect':
            success = await self.connect_to_mcp()
            await ws.send_str(json.dumps({
                'type': 'connection_status',
                'connected': success,
                'message': 'Connected to MCP server' if success else 'Failed to connect to MCP server'
            }))
        
        elif message_type == 'chat_message':
            await self.handle_chat_message(ws, data)
        
        elif message_type == 'load_history':
            await self.handle_load_history(ws)
        
        elif message_type == 'ping':
            await ws.send_str(json.dumps({'type': 'pong'}))
    
    async def handle_chat_message(self, ws: WebSocketResponse, data: Dict[str, Any]):
        """Handle chat message with streaming response"""
        if not self.mcp_client:
            await ws.send_str(json.dumps({
                'type': 'error',
                'message': 'Not connected to MCP server'
            }))
            return
        
        message = data.get('message', '')
        response_type = data.get('response_type', 'helpful')
        
        try:
            # Send typing indicator
            await ws.send_str(json.dumps({
                'type': 'typing_start'
            }))
            
            # Start streaming response
            await ws.send_str(json.dumps({
                'type': 'message_start',
                'role': 'assistant'
            }))
            
            # Stream the response
            async for chunk in self.mcp_client.call_tool_streaming('chat_stream', {
                'message': message,
                'response_type': response_type
            }):
                await ws.send_str(json.dumps({
                    'type': 'message_chunk',
                    'content': chunk
                }))
            
            # End streaming
            await ws.send_str(json.dumps({
                'type': 'message_end'
            }))
            
            await ws.send_str(json.dumps({
                'type': 'typing_end'
            }))
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await ws.send_str(json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))
            await ws.send_str(json.dumps({
                'type': 'typing_end'
            }))
    
    async def handle_load_history(self, ws: WebSocketResponse):
        """Handle loading chat history"""
        if not self.mcp_client:
            await ws.send_str(json.dumps({
                'type': 'error',
                'message': 'Not connected to MCP server'
            }))
            return
        
        try:
            await ws.send_str(json.dumps({
                'type': 'history_start'
            }))
            
            async for chunk in self.mcp_client.call_tool_streaming('chat_history', {}):
                await ws.send_str(json.dumps({
                    'type': 'history_chunk',
                    'content': chunk
                }))
            
            await ws.send_str(json.dumps({
                'type': 'history_end'
            }))
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            await ws.send_str(json.dumps({
                'type': 'error',
                'message': f'Error loading history: {str(e)}'
            }))
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await self.mcp_client.close()
        
        # Close all WebSocket connections
        for ws in list(self.websocket_connections):
            if not ws.closed:
                await ws.close()


async def create_app() -> web.Application:
    """Create and configure the web application"""
    server = MCPWebServer()
    
    app = web.Application()
    
    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Routes
    app.router.add_get('/', server.handle_index)
    app.router.add_post('/api/connect', server.handle_connect)
    app.router.add_get('/api/tools', server.handle_tools)
    app.router.add_get('/ws', server.handle_websocket)
    
    # Add CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Store server instance for cleanup
    app['mcp_server'] = server
    
    return app


async def run_server():
    """Run the web server"""
    app = await create_app()
    
    # Auto-connect to MCP server on startup
    server = app['mcp_server']
    await server.connect_to_mcp()
    
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        
        print("🚀 MCP Chat Web Server started!")
        print("📱 Open http://localhost:8080 in your browser")
        print("🔌 MCP Server: localhost:3001")
        print("⏹️  Press Ctrl+C to stop")
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down server...")
        await server.cleanup()
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\\n👋 Server stopped")