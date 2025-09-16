#!/usr/bin/env python3
"""
Simple Working MCP Web Chat Server
Creates fresh connection for each request to avoid connection issues
"""
import asyncio
import json
import http.server
import socketserver
from urllib.parse import urlparse

try:
    from client import MCPClient
except ImportError:
    import sys
    sys.path.append('.')
    from client import MCPClient


class SimpleMCPWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.')
    
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
        """Serve simple working chat interface"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MCP 聊天演示 - 简单版本</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #17a2b8; color: white; padding: 20px; text-align: center; }
        .status { padding: 10px 20px; background: #f8f9fa; border-bottom: 1px solid #ddd; text-align: center; color: #28a745; }
        .messages { height: 400px; overflow-y: auto; padding: 20px; background: #fafafa; }
        .message { margin-bottom: 15px; }
        .message.user { text-align: right; }
        .message-content { display: inline-block; padding: 10px 15px; border-radius: 20px; max-width: 70%; }
        .message.user .message-content { background: #007bff; color: white; }
        .message.assistant .message-content { background: white; border: 1px solid #ddd; }
        .message.system .message-content { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
        .message.error .message-content { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .input-area { padding: 20px; border-top: 1px solid #ddd; display: flex; gap: 10px; }
        .input-area select { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 25px; }
        .input-area button { padding: 10px 20px; background: #17a2b8; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .input-area button:disabled { background: #6c757d; cursor: not-allowed; }
        .demo-buttons { padding: 10px 20px; background: #e9ecef; display: flex; gap: 10px; flex-wrap: wrap; }
        .demo-button { padding: 5px 10px; background: white; border: 1px solid #ccc; border-radius: 15px; cursor: pointer; font-size: 0.9em; }
        .demo-button:hover { background: #f8f9fa; }
        .loading { opacity: 0.6; pointer-events: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MCP 聊天演示</h1>
            <small>简单版本 - 每次请求新连接</small>
        </div>
        
        <div class="status">
            ✅ 服务器运行正常 - 每次请求都会创建新的MCP连接
        </div>
        
        <div class="demo-buttons">
            <button class="demo-button" onclick="sendDemo('helpful')">帮助询问</button>
            <button class="demo-button" onclick="sendDemo('creative')">创意询问</button>
            <button class="demo-button" onclick="sendDemo('technical')">技术询问</button>
            <button class="demo-button" onclick="testConnection()">测试连接</button>
            <button class="demo-button" onclick="clearMessages()">清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-content">欢迎使用 MCP 聊天演示！这个版本为每次请求创建新连接，避免连接问题。</div>
            </div>
        </div>
        
        <div class="input-area">
            <select id="responseType">
                <option value="helpful">帮助性</option>
                <option value="creative">创意性</option>
                <option value="technical">技术性</option>
            </select>
            <input type="text" id="messageInput" placeholder="输入消息..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()" id="sendBtn">发送</button>
        </div>
    </div>

    <script>
        async function testConnection() {
            addMessage('system', '🔍 测试 MCP 连接...');
            
            try {
                const response = await fetch('/api/status');
                if (response.ok) {
                    const data = await response.json();
                    addMessage('system', '✅ Web服务器正常，MCP服务器: ' + data.mcp_server);
                } else {
                    addMessage('error', '❌ Web服务器响应异常');
                }
            } catch (error) {
                addMessage('error', '❌ 测试失败: ' + error.message);
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
            const input = document.getElementById('messageInput');
            const responseType = document.getElementById('responseType').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            const assistantDiv = addMessage('assistant', '正在连接MCP服务器并获取响应...');
            const sendBtn = document.getElementById('sendBtn');
            const container = document.querySelector('.container');
            
            sendBtn.disabled = true;
            container.classList.add('loading');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        message, 
                        response_type: responseType 
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    assistantDiv.textContent = data.response;
                } else {
                    assistantDiv.className = 'message-content';
                    assistantDiv.parentElement.className = 'message error';
                    assistantDiv.textContent = '❌ 错误: ' + (data.error || data.message || '未知错误');
                }
            } catch (error) {
                assistantDiv.className = 'message-content';
                assistantDiv.parentElement.className = 'message error';
                assistantDiv.textContent = '❌ 网络错误: ' + error.message;
            } finally {
                sendBtn.disabled = false;
                container.classList.remove('loading');
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
            'status': 'running',
            'mcp_server': 'localhost:3001',
            'connection_type': 'fresh_per_request'
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_connect(self):
        """Handle MCP connection test"""
        def test_mcp_connection():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._test_mcp())
            finally:
                loop.close()
        
        try:
            success, message = test_mcp_connection()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'message': message
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Connection test error: {str(e)}")
    
    async def _test_mcp(self):
        """Test MCP connection"""
        client = None
        try:
            client = MCPClient()
            await client.connect_tcp("localhost", 3001)
            init_result = await client.initialize("test-client", "1.0.0")
            await client.ping()
            return True, f"MCP连接正常: {getattr(init_result, 'serverInfo', {})}"
        except Exception as e:
            return False, f"MCP连接失败: {str(e)}"
        finally:
            if client:
                try:
                    await client.close()
                except:
                    pass
    
    def handle_chat(self):
        """Handle chat request with fresh connection"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            response_type = data.get('response_type', 'helpful')
            
            def process_chat():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._process_chat(message, response_type))
                finally:
                    loop.close()
            
            success, response_text = process_chat()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'response': response_text if success else None,
                'error': None if success else response_text
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Chat processing error: {str(e)}")
    
    async def _process_chat(self, message, response_type):
        """Process chat with fresh MCP connection"""
        client = None
        try:
            # Create fresh connection
            client = MCPClient()
            await client.connect_tcp("localhost", 3001)
            await client.initialize("chat-client", "1.0.0")
            
            # Collect streaming response
            response_parts = []
            async for chunk in client.call_tool_streaming('chat_stream', {
                'message': message,
                'response_type': response_type
            }):
                response_parts.append(chunk)
            
            if response_parts:
                return True, ' '.join(response_parts)
            else:
                return False, "收到空响应"
                
        except Exception as e:
            return False, f"处理失败: {str(e)}"
        finally:
            if client:
                try:
                    await client.close()
                except:
                    pass


def run_simple_server():
    """Run the simple working server"""
    PORT = 8085
    
    print(f"Simple MCP Web Chat Server starting on port {PORT}")
    print(f"Open http://localhost:{PORT} in your browser")
    print(f"MCP Server: localhost:3001")
    print(f"Strategy: Fresh connection per request")
    print(f"Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), SimpleMCPWebHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer stopped")


if __name__ == "__main__":
    run_simple_server()