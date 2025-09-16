#!/usr/bin/env python3
"""
MCP Server with Kimi AI Integration
Supports kimi-k2-turbo-preview and ultrathink models
"""
import asyncio
import inspect
import json
import os
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
import aiohttp

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


class KimiAIClient:
    """Kimi AI API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str = "kimi-k2-turbo-preview",
                            stream: bool = False,
                            temperature: float = 0.7,
                            max_tokens: int = 2000) -> AsyncIterator[str]:
        """
        调用 Kimi AI 聊天完成 API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        url = f"{self.base_url}/chat/completions"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Kimi API error {response.status}: {error_text}")
                
                if stream:
                    # 流式响应处理
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    choice = data['choices'][0]
                                    if 'delta' in choice and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        if content:
                                            yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    # 非流式响应
                    result = await response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        yield content
                        
        except Exception as e:
            raise Exception(f"Kimi API 调用失败: {str(e)}")


class KimiMCPServer:
    def __init__(self, name: str = "kimi-mcp-server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = False
        
        # Kimi AI 配置
        self.kimi_api_key = os.getenv('KIMI_API_KEY', '')
        self.kimi_base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        
        if not self.kimi_api_key:
            print("警告: 未设置 KIMI_API_KEY 环境变量，将使用模拟响应")
        
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
        server = await asyncio.start_server(
            self._handle_client, host, port
        )
        
        print(f"Kimi MCP Server running on {host}:{port}")
        if self.kimi_api_key:
            print(f"✅ Kimi AI API 已配置")
        else:
            print(f"⚠️  Kimi API Key 未配置，使用模拟响应")
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


def create_kimi_server():
    """创建集成 Kimi AI 的 MCP 服务器"""
    server = KimiMCPServer("kimi-mcp-server", "1.0.0")
    
    @server.tool("kimi_chat", "与 Kimi AI 模型对话", {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "用户消息"},
            "model": {"type": "string", "description": "模型名称 (kimi-k2-turbo-preview 或 ultrathink)", "default": "kimi-k2-turbo-preview"},
            "temperature": {"type": "number", "description": "温度参数 (0.0-1.0)", "default": 0.7},
            "max_tokens": {"type": "integer", "description": "最大token数", "default": 2000}
        },
        "required": ["message"]
    })
    async def kimi_chat(message: str, model: str = "kimi-k2-turbo-preview", temperature: float = 0.7, max_tokens: int = 2000):
        """与 Kimi AI 模型对话（流式）"""
        if not server.kimi_api_key:
            # 如果没有 API Key，返回模拟响应
            mock_responses = [
                f"[模拟 {model}] 收到您的消息: {message[:50]}...",
                "这是一个模拟响应，因为未配置 Kimi API Key。",
                "请设置 KIMI_API_KEY 环境变量以使用真实的 Kimi AI 模型。"
            ]
            for response in mock_responses:
                yield response
                await asyncio.sleep(0.5)
            return
        
        try:
            messages = [{"role": "user", "content": message}]
            
            async with KimiAIClient(server.kimi_api_key, server.kimi_base_url) as kimi:
                async for chunk in kimi.chat_completion(
                    messages=messages,
                    model=model,
                    stream=True,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
                    
        except Exception as e:
            yield f"Kimi AI 调用失败: {str(e)}"
    
    @server.tool("kimi_models", "获取可用的 Kimi 模型列表")
    def get_kimi_models():
        """获取可用的 Kimi AI 模型"""
        models = [
            {
                "name": "kimi-k2-turbo-preview",
                "description": "Kimi K2 Turbo 预览版 - 快速响应的对话模型",
                "max_tokens": 4096
            },
            {
                "name": "ultrathink",
                "description": "UltraThink - 深度思考模型，适合复杂推理任务",
                "max_tokens": 8192
            }
        ]
        return json.dumps(models, ensure_ascii=False, indent=2)
    
    @server.resource("config://kimi-settings", "kimi_settings", "application/json", "Kimi AI 配置信息")
    def get_kimi_settings():
        """获取 Kimi AI 配置信息"""
        return {
            "api_configured": bool(server.kimi_api_key),
            "base_url": server.kimi_base_url,
            "available_models": ["kimi-k2-turbo-preview", "ultrathink"],
            "features": ["streaming", "chat_completion"]
        }
        
    @server.prompt("kimi_system_prompt", "为 Kimi AI 生成系统提示", [
        {"name": "role", "description": "AI 角色定义", "required": False},
        {"name": "task", "description": "具体任务描述", "required": False}
    ])
    def kimi_system_prompt(role: str = "helpful assistant", task: str = "general conversation"):
        """生成 Kimi AI 系统提示"""
        return {
            "role": "system",
            "content": f"你是一个{role}，专门负责{task}。请用友善、专业且有帮助的方式回应用户。"
        }
        
    return server


async def run_kimi_server():
    """运行 Kimi MCP 服务器"""
    server = create_kimi_server()
    
    try:
        await server.start_tcp(port=3001)
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        await server.stop()


if __name__ == "__main__":
    # 检查环境变量
    print("Kimi MCP Server 启动中...")
    api_key = os.getenv('KIMI_API_KEY')
    if api_key:
        print(f"✅ 检测到 Kimi API Key: {api_key[:8]}...")
    else:
        print("⚠️  未检测到 KIMI_API_KEY 环境变量")
        print("   请设置: export KIMI_API_KEY=your_api_key")
        print("   或者: set KIMI_API_KEY=your_api_key (Windows)")
    
    asyncio.run(run_kimi_server())