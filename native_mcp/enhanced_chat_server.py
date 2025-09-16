#!/usr/bin/env python3
"""
Enhanced HTTP Server with Real MCP Connection
Provides HTTP endpoints and Server-Sent Events for streaming
"""
import asyncio
import json
import http.server
import socketserver
import threading
import time
from urllib.parse import urlparse, parse_qs

try:
    from client import MCPClient
except ImportError:
    import sys
    sys.path.append('.')
    from client import MCPClient


class MCPStreamingServer:
    def __init__(self, mcp_host="localhost", mcp_port=3001):
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.mcp_client = None
        self.connected = False
        self.loop = None
        
    async def connect_to_mcp(self):
        """Connect to MCP server"""
        try:
            if self.mcp_client:
                await self.mcp_client.close()
                
            self.mcp_client = MCPClient()
            await self.mcp_client.connect_tcp(self.mcp_host, self.mcp_port)
            init_result = await self.mcp_client.initialize("web-server", "1.0.0")
            self.connected = True
            print(f"[OK] Connected to MCP server: {getattr(init_result, 'serverInfo', {})}")
            return True
        except Exception as e:
            print(f"[FAIL] Failed to connect to MCP: {e}")
            self.connected = False
            return False
    
    async def stream_chat_response(self, message, response_type="helpful"):
        """Stream chat response from MCP server"""
        if not self.connected or not self.mcp_client:
            raise Exception("Not connected to MCP server")
            
        async for chunk in self.mcp_client.call_tool_streaming('chat_stream', {
            'message': message,
            'response_type': response_type
        }):
            yield chunk
    
    async def stream_chat_history(self):
        """Stream chat history from MCP server"""
        if not self.connected or not self.mcp_client:
            raise Exception("Not connected to MCP server")
            
        async for chunk in self.mcp_client.call_tool_streaming('chat_history', {}):
            yield chunk


# Global MCP server instance
mcp_server = MCPStreamingServer()


class MCPChatHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.')
        
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the enhanced chat interface
            self.serve_enhanced_chat_interface()
        
        elif parsed_path.path == '/api/status':
            # MCP connection status
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'connected': mcp_server.connected,
                'mcp_host': mcp_server.mcp_host,
                'mcp_port': mcp_server.mcp_port
            })
            self.wfile.write(response.encode('utf-8'))
        
        elif parsed_path.path == '/api/connect':
            # Connect to MCP server
            self.handle_mcp_connect()
        
        elif parsed_path.path == '/api/stream':
            # Server-Sent Events endpoint for streaming
            self.handle_sse_stream(parsed_path.query)
        
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/chat':
            self.handle_chat_request()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_enhanced_chat_interface(self):
        """Serve enhanced chat interface with real MCP connection"""
        html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 实时流式聊天</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh; display: flex; justify-content: center; align-items: center;
        }
        .chat-container {
            width: 90%; max-width: 800px; height: 90vh; background: white;
            border-radius: 15px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            display: flex; flex-direction: column; overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; padding: 20px; text-align: center; font-size: 1.2em; font-weight: 600;
        }
        .connection-status {
            padding: 10px 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef;
            font-size: 0.9em; display: flex; justify-content: space-between; align-items: center;
        }
        .status-indicator {
            display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px;
        }
        .status-connected { background-color: #28a745; }
        .status-disconnected { background-color: #dc3545; }
        .chat-messages {
            flex: 1; overflow-y: auto; padding: 20px; background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px; display: flex; align-items: flex-start;
        }
        .message.user { justify-content: flex-end; }
        .message-content {
            max-width: 70%; padding: 12px 16px; border-radius: 18px;
            word-wrap: break-word; line-height: 1.4;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white;
        }
        .message.assistant .message-content {
            background: white; border: 1px solid #e9ecef; color: #333;
        }
        .message.system .message-content {
            background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; font-style: italic;
        }
        .message-timestamp {
            font-size: 0.75em; color: #6c757d; margin-top: 4px;
        }
        .typing-indicator {
            display: none; align-items: center; margin-bottom: 15px;
        }
        .typing-dots {
            background: white; border: 1px solid #e9ecef; border-radius: 18px; padding: 12px 16px;
            display: flex; align-items: center;
        }
        .typing-dots span {
            height: 8px; width: 8px; background: #6c757d; border-radius: 50%;
            display: inline-block; margin-right: 5px; animation: typing 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        .chat-input-container {
            background: white; padding: 20px; border-top: 1px solid #e9ecef;
            display: flex; gap: 10px; align-items: flex-end;
        }
        .chat-input {
            flex: 1; border: 2px solid #e9ecef; border-radius: 25px; padding: 12px 16px;
            font-size: 1em; outline: none; resize: none; max-height: 100px; min-height: 44px;
            transition: border-color 0.3s;
        }
        .chat-input:focus { border-color: #4facfe; }
        .response-type-select {
            border: 2px solid #e9ecef; border-radius: 20px; padding: 8px 12px;
            font-size: 0.9em; outline: none; background: white; cursor: pointer;
        }
        .send-button {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; border: none; border-radius: 50%; width: 44px; height: 44px;
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            transition: transform 0.2s;
        }
        .send-button:hover:not(:disabled) { transform: scale(1.05); }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; }
        .demo-buttons {
            padding: 10px 20px; background: #e9ecef; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
        }
        .demo-button {
            background: white; border: 1px solid #ccc; border-radius: 15px; padding: 5px 12px;
            font-size: 0.8em; cursor: pointer; transition: all 0.2s;
        }
        .demo-button:hover { background: #f8f9fa; border-color: #4facfe; }
        .connect-button {
            background: #28a745; color: white; border: none; border-radius: 15px; padding: 5px 15px;
            cursor: pointer; font-size: 0.9em;
        }
        .connect-button:hover { background: #218838; }
        .connect-button:disabled { background: #6c757d; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">MCP 实时流式聊天</div>
        
        <div class="connection-status">
            <div>
                <span class="status-indicator status-disconnected" id="statusIndicator"></span>
                <span id="connectionStatus">未连接</span>
            </div>
            <button class="connect-button" id="connectButton" onclick="connectToMCP()">连接 MCP</button>
        </div>

        <div class="demo-buttons">
            <button class="demo-button" onclick="loadChatHistory()">加载聊天历史</button>
            <button class="demo-button" onclick="sendDemoMessage('helpful')">帮助询问</button>
            <button class="demo-button" onclick="sendDemoMessage('creative')">创意询问</button>
            <button class="demo-button" onclick="sendDemoMessage('technical')">技术询问</button>
            <button class="demo-button" onclick="clearChat()">清空聊天</button>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message system">
                <div class="message-content">
                    欢迎使用 MCP 实时流式聊天！点击"连接 MCP"开始体验。
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span></span><span></span><span></span>正在输入...
            </div>
        </div>
        
        <div class="chat-input-container">
            <select class="response-type-select" id="responseType">
                <option value="helpful">帮助性回复</option>
                <option value="creative">创意性回复</option>
                <option value="technical">技术性回复</option>
            </select>
            <textarea class="chat-input" id="chatInput" placeholder="输入你的消息..." onkeydown="handleInputKeydown(event)"></textarea>
            <button class="send-button" id="sendButton" onclick="sendMessage()" disabled>➤</button>
        </div>
    </div>

    <script>
        let isConnected = false;
        let currentEventSource = null;

        async function connectToMCP() {
            const statusIndicator = document.getElementById('statusIndicator');
            const connectionStatus = document.getElementById('connectionStatus');
            const connectButton = document.getElementById('connectButton');
            const sendButton = document.getElementById('sendButton');

            connectButton.textContent = '连接中...';
            connectButton.disabled = true;
            connectionStatus.textContent = '连接中...';

            try {
                const response = await fetch('/api/connect');
                const data = await response.json();
                
                if (data.success) {
                    isConnected = true;
                    statusIndicator.className = 'status-indicator status-connected';
                    connectionStatus.textContent = '已连接 MCP 服务器';
                    connectButton.textContent = '已连接';
                    sendButton.disabled = false;
                    addSystemMessage('成功连接到 MCP 服务器！');
                } else {
                    throw new Error(data.message || '连接失败');
                }
            } catch (error) {
                statusIndicator.className = 'status-indicator status-disconnected';
                connectionStatus.textContent = '连接失败';
                connectButton.textContent = '重新连接';
                connectButton.disabled = false;
                addSystemMessage('连接 MCP 服务器失败: ' + error.message);
            }
        }

        function addMessage(role, content) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            const timestampDiv = document.createElement('div');
            timestampDiv.className = 'message-timestamp';
            timestampDiv.textContent = new Date().toLocaleTimeString();
            
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timestampDiv);
            chatMessages.appendChild(messageDiv);
            
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return contentDiv;
        }

        function addSystemMessage(content) {
            addMessage('system', content);
        }

        function showTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
        }

        function hideTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'none';
        }

        async function sendMessage() {
            if (!isConnected) {
                addSystemMessage('请先连接到 MCP 服务器');
                return;
            }

            const chatInput = document.getElementById('chatInput');
            const responseType = document.getElementById('responseType').value;
            const message = chatInput.value.trim();

            if (!message) return;

            addMessage('user', message);
            chatInput.value = '';
            showTypingIndicator();

            try {
                const assistantContentDiv = addMessage('assistant', '');
                
                // 使用 Server-Sent Events 进行流式传输
                const eventSource = new EventSource(`/api/stream?type=chat&message=${encodeURIComponent(message)}&response_type=${responseType}`);
                currentEventSource = eventSource;
                
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'chunk') {
                        assistantContentDiv.textContent += data.content + ' ';
                        document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
                    } else if (data.type === 'end') {
                        eventSource.close();
                        hideTypingIndicator();
                    }
                };
                
                eventSource.onerror = function(event) {
                    eventSource.close();
                    hideTypingIndicator();
                    addSystemMessage('流式传输出错');
                };
                
            } catch (error) {
                hideTypingIndicator();
                addSystemMessage('发送消息时出错: ' + error.message);
            }
        }

        async function loadChatHistory() {
            if (!isConnected) {
                addSystemMessage('请先连接到 MCP 服务器');
                return;
            }

            addSystemMessage('正在加载聊天历史...');

            try {
                const eventSource = new EventSource('/api/stream?type=history');
                
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'chunk') {
                        addSystemMessage(data.content);
                    } else if (data.type === 'end') {
                        eventSource.close();
                        addSystemMessage('聊天历史加载完成');
                    }
                };
                
                eventSource.onerror = function(event) {
                    eventSource.close();
                    addSystemMessage('加载历史时出错');
                };
                
            } catch (error) {
                addSystemMessage('加载聊天历史时出错: ' + error.message);
            }
        }

        function sendDemoMessage(type) {
            const demoMessages = {
                helpful: "你能帮我理解什么是机器学习吗？",
                creative: "如何创造性地解决团队协作问题？", 
                technical: "请解释一下 REST API 的设计原则"
            };

            const chatInput = document.getElementById('chatInput');
            const responseTypeSelect = document.getElementById('responseType');
            
            chatInput.value = demoMessages[type];
            responseTypeSelect.value = type;
            
            sendMessage();
        }

        function clearChat() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = `
                <div class="message system">
                    <div class="message-content">聊天记录已清空。继续新的对话吧！</div>
                </div>
            `;
        }

        function handleInputKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // 页面加载完成后检查状态
        window.addEventListener('load', () => {
            setTimeout(connectToMCP, 500);
        });
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def handle_mcp_connect(self):
        """Handle MCP connection request"""
        def run_async_connect():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(mcp_server.connect_to_mcp())
                return result
            finally:
                loop.close()
        
        try:
            success = run_async_connect()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'message': 'Connected to MCP server' if success else 'Failed to connect to MCP server'
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Connection error: {str(e)}")
    
    def handle_sse_stream(self, query_string):
        """Handle Server-Sent Events streaming"""
        params = parse_qs(query_string)
        stream_type = params.get('type', [''])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        def run_streaming():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if stream_type == 'chat':
                    message = params.get('message', [''])[0]
                    response_type = params.get('response_type', ['helpful'])[0]
                    
                    async def stream_chat():
                        try:
                            async for chunk in mcp_server.stream_chat_response(message, response_type):
                                data = json.dumps({'type': 'chunk', 'content': chunk})
                                self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
                                self.wfile.flush()
                            
                            # End marker
                            end_data = json.dumps({'type': 'end'})
                            self.wfile.write(f"data: {end_data}\n\n".encode('utf-8'))
                            self.wfile.flush()
                        except Exception as e:
                            error_data = json.dumps({'type': 'error', 'message': str(e)})
                            self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                            self.wfile.flush()
                    
                    loop.run_until_complete(stream_chat())
                    
                elif stream_type == 'history':
                    async def stream_history():
                        try:
                            async for chunk in mcp_server.stream_chat_history():
                                data = json.dumps({'type': 'chunk', 'content': chunk})
                                self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
                                self.wfile.flush()
                            
                            # End marker
                            end_data = json.dumps({'type': 'end'})
                            self.wfile.write(f"data: {end_data}\n\n".encode('utf-8'))
                            self.wfile.flush()
                        except Exception as e:
                            error_data = json.dumps({'type': 'error', 'message': str(e)})
                            self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                            self.wfile.flush()
                    
                    loop.run_until_complete(stream_history())
                    
            finally:
                loop.close()
        
        try:
            run_streaming()
        except Exception as e:
            error_data = json.dumps({'type': 'error', 'message': str(e)})
            self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
            self.wfile.flush()
    
    def handle_chat_request(self):
        """Handle regular chat POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            response_type = data.get('response_type', 'helpful')
            
            # For fallback, generate a simple response
            demo_response = f"关于 '{message[:30]}...' 的回复，这是一个演示响应。"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': True,
                'response': demo_response
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error processing request: {str(e)}")


def run_server():
    """Run the enhanced HTTP server with MCP connection"""
    PORT = 8081
    
    print(f"MCP Chat Server starting...")
    print(f"Open http://localhost:{PORT} in your browser")
    print(f"MCP Server: localhost:3001")
    print(f"Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), MCPChatHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer stopped")


if __name__ == "__main__":
    run_server()