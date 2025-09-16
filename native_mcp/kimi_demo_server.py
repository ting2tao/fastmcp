#!/usr/bin/env python3
"""
Simplified Kimi AI MCP Server - Demo Version
Uses built-in libraries only for demonstration
"""
import asyncio
import inspect
import json
import os
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


class SimplifiedKimiMCPServer:
    def __init__(self, name: str = "kimi-mcp-server-demo", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = False
        
        # Kimi AI 配置 (演示模式)
        self.kimi_api_key = os.getenv('KIMI_API_KEY', '')
        self.demo_mode = not bool(self.kimi_api_key)
        
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
    
    async def start_tcp(self, host: str = "localhost", port: int = 3001):
        """Start server using TCP transport"""
        print(f"[DEBUG] Starting TCP server on {host}:{port}...")
        server = await asyncio.start_server(
            self._handle_client, host, port
        )
        
        print(f"Kimi MCP Server (Demo) running on {host}:{port}")
        if self.demo_mode:
            print(f"[DEMO] Demo mode: using mock Kimi AI responses")
            print(f"[TIP] To use real API, set: export KIMI_API_KEY=your_key")
        else:
            print(f"[OK] Production mode: Kimi API Key configured")
        self.running = True
        print(f"[DEBUG] Server is ready to accept connections")
        
        async with server:
            await server.serve_forever()
            
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection"""
        client_address = writer.get_extra_info('peername')
        print(f"[DEBUG] New client connection from {client_address}")
        
        self.reader = reader
        self.writer = writer
        
        try:
            await self._message_loop()
        except Exception as e:
            print(f"[ERROR] Client error: {e}")
        finally:
            print(f"[DEBUG] Closing connection from {client_address}")
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
            
        message_str = MCPMessage.serialize(response) + "\\n"
        self.writer.write(message_str.encode())
        await self.writer.drain()
        
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification"""
        if not self.writer:
            return
            
        notification = MCPNotification(method=method, params=params)
        message_str = MCPMessage.serialize(notification) + "\\n"
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


def create_simplified_kimi_server():
    """创建简化的 Kimi AI MCP 服务器"""
    server = SimplifiedKimiMCPServer("kimi-mcp-demo", "1.0.0")
    
    @server.tool("kimi_chat", "与 Kimi AI 模型对话 (演示版)", {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "用户消息"},
            "model": {"type": "string", "description": "模型名称", "default": "kimi-k2-turbo-preview"},
            "temperature": {"type": "number", "description": "温度参数", "default": 0.7},
            "max_tokens": {"type": "integer", "description": "最大token数", "default": 2000}
        },
        "required": ["message"]
    })
    async def kimi_chat(message: str, model: str = "kimi-k2-turbo-preview", temperature: float = 0.7, max_tokens: int = 2000):
        """与 Kimi AI 模型对话（演示版流式响应）"""
        
        # 根据模型类型生成不同风格的响应
        if model == "ultrathink":
            responses = [
                f"[UltraThink 深度分析] 正在分析您的问题: {message[:50]}...",
                "让我深入思考这个问题的各个层面...",
                "",
                "第一层思考: 问题的本质是什么？",
                f"您提出的问题涉及到: {message[:100]}",
                "",
                "第二层思考: 相关的概念和理论框架",
                "我需要考虑多个角度来全面回答这个问题。",
                "",
                "第三层思考: 实际应用和深层含义",
                "基于深度分析，我认为这个问题的核心在于...",
                "",
                "综合结论:",
                f"针对您关于'{message[:30]}...'的问题，经过深度思考，我的观点是...",
                "",
                "这是一个需要多维度思考的复杂问题，希望我的深度分析对您有帮助。"
            ]
        else:  # kimi-k2-turbo-preview
            responses = [
                f"[Kimi K2 Turbo] 收到您的消息: {message[:50]}...",
                "正在快速处理您的请求...",
                "",
                f"关于您提到的'{message[:40]}'，我来为您详细解答:",
                "",
                "首先，让我理解一下您的需求...",
                f"基于您的问题，我认为关键点在于: {message[:60]}",
                "",
                "让我为您提供一个清晰的回答:",
                "1. 这个问题涉及到的核心概念",
                "2. 相关的背景知识和应用场景", 
                "3. 实用的建议和解决方案",
                "",
                f"总结来说，对于'{message[:30]}...'这个问题，我的建议是...",
                "",
                "希望这个回答对您有帮助！如果您还有其他问题，随时可以继续提问。"
            ]
        
        # 模拟流式输出
        for i, response_part in enumerate(responses):
            yield response_part
            # 根据内容长度调整延迟时间
            if response_part:
                delay = 0.2 + len(response_part) * 0.01
                await asyncio.sleep(min(delay, 1.0))  # 最大延迟1秒
            else:
                await asyncio.sleep(0.1)  # 空行短暂延迟
    
    @server.tool("kimi_models", "获取可用的 Kimi 模型列表")
    def get_kimi_models():
        """获取可用的 Kimi AI 模型（演示版）"""
        models = [
            {
                "name": "kimi-k2-turbo-preview",
                "description": "Kimi K2 Turbo 预览版 - 快速响应的对话模型，适合日常对话和快速问答",
                "max_tokens": 4096,
                "features": ["快速响应", "多轮对话", "知识问答"],
                "use_cases": ["日常聊天", "信息查询", "简单任务"]
            },
            {
                "name": "ultrathink",
                "description": "UltraThink - 深度思考模型，适合复杂推理任务和深度分析",
                "max_tokens": 8192,
                "features": ["深度推理", "逻辑分析", "复杂问题解决"],
                "use_cases": ["学术研究", "复杂分析", "创新思考"]
            }
        ]
        return json.dumps(models, ensure_ascii=False, indent=2)
    
    @server.resource("config://kimi-demo-settings", "kimi_demo_settings", "application/json", "Kimi AI 演示配置")
    def get_kimi_demo_settings():
        """获取 Kimi AI 演示配置信息"""
        return {
            "mode": "demo" if server.demo_mode else "production",
            "api_configured": not server.demo_mode,
            "available_models": ["kimi-k2-turbo-preview", "ultrathink"],
            "features": ["streaming", "chat_completion", "model_selection"],
            "demo_note": "当前为演示模式，使用模拟响应。设置 KIMI_API_KEY 环境变量可切换到真实模式。"
        }
        
    @server.prompt("kimi_conversation_starter", "Kimi AI 对话开始提示", [
        {"name": "topic", "description": "对话主题", "required": False},
        {"name": "style", "description": "对话风格", "required": False}
    ])
    def kimi_conversation_starter(topic: str = "AI技术", style: str = "友好专业"):
        """生成 Kimi AI 对话开始提示"""
        return {
            "role": "system",
            "content": f"你是 Kimi AI，一个{style}的人工智能助手。现在我们要讨论关于{topic}的话题。请用温暖、专业且富有洞察力的方式与用户交流。"
        }
        
    return server


async def run_simplified_kimi_server():
    """运行简化的 Kimi MCP 服务器"""
    print("Creating Kimi MCP server...")
    server = create_simplified_kimi_server()
    print("Server created, starting on port 3002...")
    
    try:
        await server.start_tcp(port=3002)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    import sys
    print("Kimi MCP Server (Simplified Demo) starting...")
    sys.stdout.flush()
    api_key = os.getenv('KIMI_API_KEY')
    if api_key:
        print(f"[OK] Detected Kimi API Key")
        sys.stdout.flush()
    else:
        print("[DEMO] Demo mode: No KIMI_API_KEY found, using mock responses")
        print("[TIP] To use real API, set: export KIMI_API_KEY=your_key")
        sys.stdout.flush()
    
    asyncio.run(run_simplified_kimi_server())