#!/usr/bin/env python3
"""
Simple Web Server that connects to MCP for streaming chat
"""
import asyncio
import json
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

try:
    from client import MCPClient
except ImportError:
    import sys
    sys.path.append('.')
    from client import MCPClient


class MCPWebHandler(http.server.SimpleHTTPRequestHandler):
    # Class-level MCP client
    mcp_client = None
    mcp_connected = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.')
    
    @classmethod
    async def connect_mcp(cls):
        """Connect to MCP server"""
        try:
            if cls.mcp_client:
                await cls.mcp_client.close()
            
            cls.mcp_client = MCPClient()
            await cls.mcp_client.connect_tcp("localhost", 3001)
            init_result = await cls.mcp_client.initialize("web-client", "1.0.0")
            cls.mcp_connected = True
            print(f"[OK] Connected to MCP: {getattr(init_result, 'serverInfo', {})}")
            return True
        except Exception as e:
            print(f"[FAIL] MCP connection failed: {e}")
            cls.mcp_connected = False
            return False
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_chat_page()
        elif parsed_path.path == '/api/status':
            self.handle_status()
        elif parsed_path.path == '/api/connect':
            self.handle_connect()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/chat':
            self.handle_chat()
        else:
            self.send_error(404)
    
    def serve_chat_page(self):
        """Serve the web chat interface"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MCP 流式聊天演示</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .status { padding: 10px 20px; background: #f8f9fa; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; }
        .connected { background: #28a745; }
        .disconnected { background: #dc3545; }
        .messages { height: 400px; overflow-y: auto; padding: 20px; background: #fafafa; }
        .message { margin-bottom: 15px; }
        .message.user { text-align: right; }
        .message-content { display: inline-block; padding: 10px 15px; border-radius: 20px; max-width: 70%; }
        .message.user .message-content { background: #007bff; color: white; }
        .message.assistant .message-content { background: white; border: 1px solid #ddd; }
        .message.system .message-content { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; font-style: italic; }
        .input-area { padding: 20px; border-top: 1px solid #ddd; display: flex; gap: 10px; }
        .input-area select { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 25px; }
        .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .input-area button:disabled { background: #6c757d; cursor: not-allowed; }
        .demo-buttons { padding: 10px 20px; background: #e9ecef; display: flex; gap: 10px; flex-wrap: wrap; }
        .demo-button { padding: 5px 10px; background: white; border: 1px solid #ccc; border-radius: 15px; cursor: pointer; font-size: 0.9em; }
        .demo-button:hover { background: #f8f9fa; }
        .connect-btn { background: #28a745; color: white; border: none; padding: 5px 15px; border-radius: 15px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MCP 流式聊天演示</h1>
        </div>
        
        <div class="status">
            <div style="display: flex; align-items: center;">
                <span class="status-dot disconnected" id="statusDot"></span>
                <span id="statusText">未连接</span>
            </div>
            <button class="connect-btn" onclick="connectMCP()" id="connectBtn">连接 MCP</button>
        </div>
        
        <div class="demo-buttons">
            <button class="demo-button" onclick="sendDemo('helpful')">💡 帮助询问</button>
            <button class="demo-button" onclick="sendDemo('creative')">🎨 创意询问</button>
            <button class="demo-button" onclick="sendDemo('technical')">🔧 技术询问</button>
            <button class="demo-button" onclick="clearMessages()">🗑️ 清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-content">欢迎使用 MCP 流式聊天演示！请先连接到 MCP 服务器。</div>
            </div>
        </div>
        
        <div class="input-area">
            <select id="responseType">
                <option value="helpful">帮助性</option>
                <option value="creative">创意性</option>
                <option value="technical">技术性</option>
            </select>
            <input type="text" id="messageInput" placeholder="输入消息..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()" id="sendBtn" disabled>发送</button>
        </div>
    </div>

    <script>
        let connected = false;

        async function connectMCP() {
            const btn = document.getElementById('connectBtn');
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            const sendBtn = document.getElementById('sendBtn');
            
            btn.textContent = '连接中...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/connect');
                const data = await response.json();
                
                if (data.success) {
                    connected = true;
                    statusDot.className = 'status-dot connected';
                    statusText.textContent = '已连接';
                    btn.textContent = '已连接';
                    sendBtn.disabled = false;
                    addMessage('system', '✅ 成功连接到 MCP 服务器！');
                } else {
                    throw new Error(data.message || '连接失败');
                }
            } catch (error) {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = '连接失败';
                btn.textContent = '重新连接';
                btn.disabled = false;
                addMessage('system', '❌ 连接失败: ' + error.message);
            }
        }

        function addMessage(role, content) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.innerHTML = `<div class="message-content">${content}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div.querySelector('.message-content');
        }

        async function sendMessage() {
            if (!connected) {
                addMessage('system', '请先连接到 MCP 服务器');
                return;
            }

            const input = document.getElementById('messageInput');
            const responseType = document.getElementById('responseType').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            const assistantDiv = addMessage('assistant', '正在输入...');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, response_type: responseType })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    assistantDiv.textContent = data.response;
                } else {
                    assistantDiv.textContent = '❌ 错误: ' + (data.error || '未知错误');
                }
            } catch (error) {
                assistantDiv.textContent = '❌ 网络错误: ' + error.message;
            }
        }

        function sendDemo(type) {
            const demos = {
                helpful: '你能帮我理解什么是机器学习吗？',
                creative: '如何创造性地解决团队协作问题？',
                technical: '请解释一下 REST API 的设计原则'
            };
            
            document.getElementById('messageInput').value = demos[type];
            document.getElementById('responseType').value = type;
            sendMessage();
        }

        function clearMessages() {
            document.getElementById('messages').innerHTML = `
                <div class="message system">
                    <div class="message-content">聊天记录已清空</div>
                </div>
            `;
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        // 页面加载后自动连接
        window.addEventListener('load', () => {
            setTimeout(connectMCP, 500);
        });
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_status(self):
        """Handle status request"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps({
            'connected': self.mcp_connected,
            'server': 'localhost:3001'
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_connect(self):
        """Handle MCP connection request"""
        def run_connect():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.connect_mcp())
            finally:
                loop.close()
        
        try:
            success = run_connect()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'message': 'Connected' if success else 'Connection failed'
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_chat(self):
        """Handle chat request"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            response_type = data.get('response_type', 'helpful')
            
            def run_chat():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.get_chat_response(message, response_type))
                finally:
                    loop.close()
            
            if self.mcp_connected and self.mcp_client:
                response_text = run_chat()
            else:
                response_text = "MCP 服务器未连接，无法处理请求"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': True,
                'response': response_text
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    async def get_chat_response(self, message, response_type):
        """Get streaming chat response from MCP"""
        if not self.mcp_client or not self.mcp_connected:
            return "MCP 客户端未连接"
        
        try:
            response_parts = []
            async for chunk in self.mcp_client.call_tool_streaming('chat_stream', {
                'message': message,
                'response_type': response_type
            }):
                response_parts.append(chunk)
            
            return ' '.join(response_parts)
            
        except Exception as e:
            return f"错误: {str(e)}"


def run_server():
    """Run the web server"""
    PORT = 8082  # Use a different port to avoid conflicts
    
    print(f"MCP Web Chat Server starting on port {PORT}")
    print(f"Open http://localhost:{PORT} in your browser")
    print(f"MCP Server: localhost:3001")
    print(f"Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), MCPWebHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer stopped")


if __name__ == "__main__":
    run_server()