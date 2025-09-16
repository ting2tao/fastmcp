#!/usr/bin/env python3
"""
Enhanced Web Chat Server for Kimi AI MCP Integration
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


class KimiWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.')
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_kimi_chat_page()
        elif parsed_path.path == '/api/status':
            self.handle_status()
        elif parsed_path.path == '/api/models':
            self.handle_models()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/chat':
            self.handle_chat()
        else:
            self.send_error(404)
    
    def serve_kimi_chat_page(self):
        """Serve Kimi AI chat interface"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kimi AI MCP 聊天界面</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 900px; margin: 0 auto; background: white; border-radius: 15px; 
            overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.2);
        }
        .header { 
            background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); 
            color: white; padding: 25px; text-align: center; 
        }
        .header h1 { margin: 0; font-size: 1.8em; }
        .header .subtitle { font-size: 0.9em; opacity: 0.9; margin-top: 5px; }
        .model-selector {
            padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #ddd;
            display: flex; align-items: center; gap: 15px; flex-wrap: wrap;
        }
        .model-selector label { font-weight: 600; color: #495057; }
        .model-selector select { 
            padding: 8px 12px; border: 2px solid #e9ecef; border-radius: 8px; 
            background: white; font-size: 0.9em; min-width: 200px;
        }
        .model-info { font-size: 0.8em; color: #6c757d; flex-grow: 1; }
        .status { 
            padding: 10px 20px; background: #d4edda; border-bottom: 1px solid #c3e6cb; 
            text-align: center; color: #155724; font-weight: 500;
        }
        .messages { 
            height: 450px; overflow-y: auto; padding: 20px; background: #fafafa;
        }
        .message { margin-bottom: 20px; display: flex; align-items: flex-start; gap: 12px; }
        .message.user { flex-direction: row-reverse; }
        .message-avatar {
            width: 36px; height: 36px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; color: white; font-weight: bold;
            font-size: 14px;
        }
        .message.user .message-avatar { background: #007bff; }
        .message.assistant .message-avatar { background: #28a745; }
        .message.system .message-avatar { background: #6c757d; }
        .message.error .message-avatar { background: #dc3545; }
        .message-content { 
            max-width: 70%; padding: 12px 16px; border-radius: 18px; 
            word-wrap: break-word; line-height: 1.5; position: relative;
        }
        .message.user .message-content { 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
            color: white; 
        }
        .message.assistant .message-content { 
            background: white; border: 1px solid #e9ecef; color: #333;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .message.system .message-content { 
            background: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; 
        }
        .message.error .message-content { 
            background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
        }
        .message-timestamp { 
            font-size: 0.7em; color: #6c757d; margin-top: 5px; 
            text-align: right;
        }
        .message.user .message-timestamp { text-align: left; }
        .input-area { 
            padding: 20px; border-top: 1px solid #ddd; display: flex; gap: 12px; 
            background: white;
        }
        .input-area textarea { 
            flex: 1; padding: 12px 16px; border: 2px solid #e9ecef; border-radius: 25px; 
            font-size: 1em; outline: none; resize: none; min-height: 44px; max-height: 120px;
            transition: border-color 0.3s; font-family: inherit;
        }
        .input-area textarea:focus { border-color: #FF6B6B; }
        .input-area button { 
            padding: 12px 24px; background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); 
            color: white; border: none; border-radius: 25px; cursor: pointer; 
            font-weight: 600; transition: transform 0.2s, box-shadow 0.2s;
        }
        .input-area button:hover:not(:disabled) { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
        }
        .input-area button:disabled { 
            opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none;
        }
        .demo-buttons { 
            padding: 15px 20px; background: #e9ecef; display: flex; gap: 10px; 
            flex-wrap: wrap; justify-content: center;
        }
        .demo-button { 
            padding: 8px 16px; background: white; border: 1px solid #ccc; 
            border-radius: 20px; cursor: pointer; font-size: 0.85em;
            transition: all 0.2s; white-space: nowrap;
        }
        .demo-button:hover { 
            background: #f8f9fa; border-color: #FF6B6B; 
            transform: translateY(-1px);
        }
        .loading { opacity: 0.6; pointer-events: none; }
        .typing-indicator { 
            display: none; align-items: center; gap: 8px; margin-bottom: 15px; 
        }
        .typing-dots { 
            display: flex; gap: 4px;
        }
        .typing-dots span { 
            width: 8px; height: 8px; background: #6c757d; border-radius: 50%; 
            animation: typing 1.4s infinite ease-in-out both;
        }
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        .typing-dots span:nth-child(3) { animation-delay: 0s; }
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        .model-badge {
            display: inline-block; background: #FF6B6B; color: white; 
            padding: 2px 8px; border-radius: 10px; font-size: 0.7em; 
            margin-left: 8px; font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Kimi AI MCP 聊天</h1>
            <div class="subtitle">支持 kimi-k2-turbo-preview 和 ultrathink 模型</div>
        </div>
        
        <div class="model-selector">
            <label for="modelSelect">选择模型:</label>
            <select id="modelSelect" onchange="updateModelInfo()">
                <option value="kimi-k2-turbo-preview">Kimi K2 Turbo Preview</option>
                <option value="ultrathink">UltraThink</option>
            </select>
            <div class="model-info" id="modelInfo">
                快速响应的对话模型，适合日常对话
            </div>
        </div>
        
        <div class="status" id="status">
            🚀 Kimi AI MCP 服务器就绪
        </div>
        
        <div class="demo-buttons">
            <button class="demo-button" onclick="sendDemo('explain')">🧠 解释复杂概念</button>
            <button class="demo-button" onclick="sendDemo('creative')">🎨 创意写作</button>
            <button class="demo-button" onclick="sendDemo('analysis')">📊 深度分析</button>
            <button class="demo-button" onclick="sendDemo('code')">💻 编程助手</button>
            <button class="demo-button" onclick="testModels()">🔧 测试模型</button>
            <button class="demo-button" onclick="clearMessages()">🗑️ 清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    欢迎使用 Kimi AI MCP 聊天界面！您可以选择不同的模型进行对话。
                    <br><br>
                    <strong>kimi-k2-turbo-preview:</strong> 快速响应，适合日常对话<br>
                    <strong>ultrathink:</strong> 深度思考，适合复杂推理任务
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="message-avatar" style="background: #28a745;">AI</div>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <span style="margin-left: 8px; color: #6c757d;">正在思考...</span>
        </div>
        
        <div class="input-area">
            <textarea 
                id="messageInput" 
                placeholder="输入您的消息，体验 Kimi AI 的智能对话..."
                onkeydown="handleKeyPress(event)"
            ></textarea>
            <button onclick="sendMessage()" id="sendBtn">发送</button>
        </div>
    </div>

    <script>
        const modelDescriptions = {
            'kimi-k2-turbo-preview': '快速响应的对话模型，适合日常对话',
            'ultrathink': '深度思考模型，适合复杂推理任务'
        };

        function updateModelInfo() {
            const select = document.getElementById('modelSelect');
            const info = document.getElementById('modelInfo');
            info.textContent = modelDescriptions[select.value];
        }

        function addMessage(role, content, model = null) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${role}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = role === 'user' ? '👤' : role === 'assistant' ? '🤖' : role === 'system' ? 'ℹ️' : '❌';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.innerHTML = content + (model ? `<span class="model-badge">${model}</span>` : '');
            
            const timestamp = document.createElement('div');
            timestamp.className = 'message-timestamp';
            timestamp.textContent = new Date().toLocaleTimeString();
            
            div.appendChild(avatar);
            div.appendChild(messageContent);
            messageContent.appendChild(timestamp);
            
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            
            return messageContent;
        }

        function showTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }

        function hideTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'none';
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const modelSelect = document.getElementById('modelSelect');
            const message = input.value.trim();
            
            if (!message) return;
            
            const selectedModel = modelSelect.value;
            
            addMessage('user', message);
            input.value = '';
            
            showTypingIndicator();
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
                        model: selectedModel,
                        temperature: 0.7,
                        max_tokens: 2000
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('assistant', data.response, selectedModel);
                } else {
                    addMessage('error', '❌ 错误: ' + (data.error || '未知错误'));
                }
            } catch (error) {
                addMessage('error', '❌ 网络错误: ' + error.message);
            } finally {
                hideTypingIndicator();
                sendBtn.disabled = false;
                container.classList.remove('loading');
            }
        }

        function sendDemo(type) {
            const demos = {
                explain: '请详细解释什么是量子计算，以及它与传统计算的区别',
                creative: '写一个关于人工智能和人类友谊的短故事',
                analysis: '分析一下当前人工智能技术的发展趋势和潜在影响',
                code: '用Python写一个简单的文件压缩程序'
            };
            
            document.getElementById('messageInput').value = demos[type];
            sendMessage();
        }

        async function testModels() {
            addMessage('system', '🔧 正在测试可用模型...');
            
            try {
                const response = await fetch('/api/models');
                if (response.ok) {
                    const data = await response.json();
                    let modelList = '<strong>可用模型:</strong><br>';
                    data.models.forEach(model => {
                        modelList += `<br>📋 <strong>${model.name}</strong><br>&nbsp;&nbsp;&nbsp;&nbsp;${model.description}`;
                    });
                    addMessage('system', modelList);
                } else {
                    addMessage('error', '❌ 获取模型列表失败');
                }
            } catch (error) {
                addMessage('error', '❌ 测试失败: ' + error.message);
            }
        }

        function clearMessages() {
            document.getElementById('messages').innerHTML = `
                <div class="message system">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">聊天记录已清空，可以开始新的对话了！</div>
                </div>
            `;
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // 页面加载完成后的初始化
        window.addEventListener('load', () => {
            updateModelInfo();
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
            'status': 'running',
            'mcp_server': 'localhost:3002',
            'server_type': 'kimi_ai_mcp',
            'models_supported': ['kimi-k2-turbo-preview', 'ultrathink']
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_models(self):
        """Handle models list request"""
        def get_models():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._get_models())
            finally:
                loop.close()
        
        try:
            models_data = get_models()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(models_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Models request error: {str(e)}")
    
    async def _get_models(self):
        """Get models from MCP server"""
        client = None
        try:
            client = MCPClient()
            await client.connect_tcp("localhost", 3002)
            await client.initialize("models-client", "1.0.0")
            
            # Call the kimi_models tool
            result = await client.call_tool("kimi_models", {})
            models_info = json.loads(result['content'][0]['text'])
            
            return json.dumps({'models': models_info})
            
        except Exception as e:
            return json.dumps({
                'models': [
                    {
                        'name': 'kimi-k2-turbo-preview',
                        'description': 'Kimi K2 Turbo 预览版 - 快速响应的对话模型'
                    },
                    {
                        'name': 'ultrathink', 
                        'description': 'UltraThink - 深度思考模型，适合复杂推理任务'
                    }
                ],
                'error': str(e)
            })
        finally:
            if client:
                try:
                    await client.close()
                except:
                    pass
    
    def handle_chat(self):
        """Handle chat request with Kimi AI"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            model = data.get('model', 'kimi-k2-turbo-preview')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 2000)
            
            def process_kimi_chat():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self._process_kimi_chat(message, model, temperature, max_tokens)
                    )
                finally:
                    loop.close()
            
            success, response_text = process_kimi_chat()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'response': response_text if success else None,
                'error': None if success else response_text,
                'model': model
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Chat processing error: {str(e)}")
    
    async def _process_kimi_chat(self, message, model, temperature, max_tokens):
        """Process chat with Kimi AI via MCP"""
        client = None
        try:
            # Create fresh connection
            client = MCPClient()
            await client.connect_tcp("localhost", 3002)
            await client.initialize("kimi-chat-client", "1.0.0")
            
            # Collect streaming response
            response_parts = []
            async for chunk in client.call_tool_streaming('kimi_chat', {
                'message': message,
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens
            }):
                response_parts.append(chunk)
            
            if response_parts:
                return True, ''.join(response_parts)
            else:
                return False, "收到空响应"
                
        except Exception as e:
            return False, f"Kimi AI 调用失败: {str(e)}"
        finally:
            if client:
                try:
                    await client.close()
                except:
                    pass


def run_kimi_web_server():
    """Run the Kimi AI web server"""
    PORT = 8087
    
    print(f"[Kimi AI] MCP Web Server starting on port {PORT}")
    print(f"[Web] Open http://localhost:{PORT} in your browser")
    print(f"[MCP] MCP Server: localhost:3002 (Kimi AI enabled)")
    print(f"[Models] kimi-k2-turbo-preview, ultrathink")
    print(f"[Control] Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), KimiWebHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\n[STOP] Server stopped")


if __name__ == "__main__":
    run_kimi_web_server()