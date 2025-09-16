#!/usr/bin/env python3
"""
Real Kimi AI Integration - Calls actual Kimi API
Uses urllib.request for HTTP calls to avoid external dependencies
"""
import asyncio
import json
import http.server
import socketserver
from urllib.parse import urlparse
import urllib.request
import urllib.error
import os
import time
import ssl

class RealKimiAI:
    """Real Kimi AI API client using urllib"""
    
    def __init__(self):
        self.api_key = os.getenv('KIMI_API_KEY', '')
        self.base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        self.has_api_key = bool(self.api_key)
        
    async def chat_with_kimi(self, message: str, model: str = "kimi-k2-turbo-preview", **kwargs):
        """Call real Kimi AI API or fallback to demo"""
        
        if not self.has_api_key:
            # Fallback to demo mode
            async for chunk in self._demo_response(message, model):
                yield chunk
            return
            
        try:
            # Call real Kimi AI API
            async for chunk in self._call_real_kimi_api(message, model, **kwargs):
                yield chunk
        except Exception as e:
            yield f"[ERROR] Kimi AI API调用失败: {str(e)}"
            yield f"[FALLBACK] 切换到演示模式..."
            # Fallback to demo on error
            async for chunk in self._demo_response(message, model):
                yield chunk
    
    async def _call_real_kimi_api(self, message: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        """Call the real Kimi AI API"""
        
        # Prepare the API request
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Map our model names to Kimi's model names
        kimi_model_map = {
            'kimi-k2-turbo-preview': 'moonshot-v1-8k',  # Adjust based on actual Kimi model names
            'ultrathink': 'moonshot-v1-32k'  # Adjust based on actual Kimi model names
        }
        
        actual_model = kimi_model_map.get(model, 'moonshot-v1-8k')
        
        data = {
            "model": actual_model,
            "messages": [
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # Enable streaming
        }
        
        # Make the API call
        request = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        try:
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Make the streaming request
            with urllib.request.urlopen(request, context=ssl_context) as response:
                yield f"[{model.upper()}] 连接到 Kimi AI API 成功"
                yield f"[API] 模型: {actual_model}, 开始接收响应..."
                yield ""
                
                # Read streaming response
                buffer = ""
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data_obj = json.loads(data_str)
                            if 'choices' in data_obj and len(data_obj['choices']) > 0:
                                delta = data_obj['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    buffer += content
                                    yield content
                                    await asyncio.sleep(0.01)  # Small delay for streaming effect
                        except json.JSONDecodeError:
                            continue
                            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            yield f"[ERROR] Kimi API HTTP错误 {e.code}: {error_body}"
        except urllib.error.URLError as e:
            yield f"[ERROR] Kimi API 连接错误: {str(e)}"
        except Exception as e:
            yield f"[ERROR] Kimi API 调用异常: {str(e)}"
    
    async def _demo_response(self, message: str, model: str):
        """Fallback demo response when API key not available"""
        
        if model == "ultrathink":
            responses = [
                f"[UltraThink 演示模式] 分析问题: {message[:50]}...",
                "注意: 当前为演示模式，请设置 KIMI_API_KEY 环境变量使用真实 API",
                "",
                "第一层思考: 问题分析",
                f"您的问题: {message[:100]}",
                "",
                "第二层思考: 深度分析",
                "这需要综合考虑多个角度...",
                "",
                "第三层思考: 结论",
                "基于分析，我的观点是...",
                "",
                "[演示模式] 要获得真实的 UltraThink 响应，请配置 Kimi API Key"
            ]
        else:  # kimi-k2-turbo-preview
            responses = [
                f"[Kimi K2 演示模式] 处理消息: {message[:50]}...",
                "注意: 当前为演示模式，请设置 KIMI_API_KEY 环境变量使用真实 API",
                "",
                f"关于您的问题: {message[:40]}",
                "",
                "这是一个演示响应，展示了:",
                "1. 快速响应的特点",
                "2. 智能对话的能力",
                "3. 多轮交互的支持",
                "",
                f"[演示模式] 要获得真实的 Kimi K2 响应，请配置 Kimi API Key"
            ]
        
        for response_part in responses:
            yield response_part
            if response_part:
                await asyncio.sleep(0.1 + len(response_part) * 0.005)
            else:
                await asyncio.sleep(0.05)


class RealKimiWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.kimi_ai = RealKimiAI()
        super().__init__(*args, directory='.')
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_real_kimi_page()
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
    
    def serve_real_kimi_page(self):
        """Serve the real Kimi AI integration page"""
        api_status = "已配置 API Key" if self.kimi_ai.has_api_key else "未配置 API Key (演示模式)"
        status_color = "#28a745" if self.kimi_ai.has_api_key else "#ffc107"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>真实 Kimi AI 集成</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 900px; margin: 0 auto; background: white; border-radius: 15px; 
            overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.2);
        }}
        .header {{ 
            background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); 
            color: white; padding: 25px; text-align: center; 
        }}
        .header h1 {{ margin: 0; font-size: 1.8em; }}
        .header .subtitle {{ font-size: 0.9em; opacity: 0.9; margin-top: 5px; }}
        .api-status {{ 
            padding: 12px 20px; background: {status_color}; color: white;
            text-align: center; font-weight: 600;
        }}
        .model-selector {{
            padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #ddd;
            display: flex; align-items: center; gap: 15px; flex-wrap: wrap;
        }}
        .model-selector label {{ font-weight: 600; color: #495057; }}
        .model-selector select {{ 
            padding: 8px 12px; border: 2px solid #e9ecef; border-radius: 8px; 
            background: white; font-size: 0.9em; min-width: 200px;
        }}
        .model-info {{ font-size: 0.8em; color: #6c757d; flex-grow: 1; }}
        .messages {{ 
            height: 450px; overflow-y: auto; padding: 20px; background: #fafafa;
        }}
        .message {{ margin-bottom: 20px; display: flex; align-items: flex-start; gap: 12px; }}
        .message.user {{ flex-direction: row-reverse; }}
        .message-avatar {{
            width: 36px; height: 36px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; color: white; font-weight: bold;
            font-size: 14px;
        }}
        .message.user .message-avatar {{ background: #007bff; }}
        .message.assistant .message-avatar {{ background: #28a745; }}
        .message.system .message-avatar {{ background: #6c757d; }}
        .message.error .message-avatar {{ background: #dc3545; }}
        .message-content {{ 
            max-width: 70%; padding: 12px 16px; border-radius: 18px; 
            word-wrap: break-word; line-height: 1.5; position: relative;
            white-space: pre-line;
        }}
        .message.user .message-content {{ 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
            color: white; 
        }}
        .message.assistant .message-content {{ 
            background: white; border: 1px solid #e9ecef; color: #333;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .message.system .message-content {{ 
            background: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; 
        }}
        .message.error .message-content {{ 
            background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
        }}
        .model-badge {{
            display: inline-block; background: #FF6B6B; color: white; 
            padding: 2px 8px; border-radius: 10px; font-size: 0.7em; 
            margin-left: 8px; font-weight: 500;
        }}
        .input-area {{ 
            padding: 20px; border-top: 1px solid #ddd; display: flex; gap: 12px; 
            background: white;
        }}
        .input-area textarea {{ 
            flex: 1; padding: 12px 16px; border: 2px solid #e9ecef; border-radius: 25px; 
            font-size: 1em; outline: none; resize: none; min-height: 44px; max-height: 120px;
            transition: border-color 0.3s; font-family: inherit;
        }}
        .input-area textarea:focus {{ border-color: #FF6B6B; }}
        .input-area button {{ 
            padding: 12px 24px; background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); 
            color: white; border: none; border-radius: 25px; cursor: pointer; 
            font-weight: 600; transition: transform 0.2s, box-shadow 0.2s;
        }}
        .input-area button:hover:not(:disabled) {{ 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
        }}
        .input-area button:disabled {{ 
            opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none;
        }}
        .demo-buttons {{ 
            padding: 15px 20px; background: #e9ecef; display: flex; gap: 10px; 
            flex-wrap: wrap; justify-content: center;
        }}
        .demo-button {{ 
            padding: 8px 16px; background: white; border: 1px solid #ccc; 
            border-radius: 20px; cursor: pointer; font-size: 0.85em;
            transition: all 0.2s; white-space: nowrap;
        }}
        .demo-button:hover {{ 
            background: #f8f9fa; border-color: #FF6B6B; 
            transform: translateY(-1px);
        }}
        .loading {{ opacity: 0.6; pointer-events: none; }}
        .api-key-info {{
            padding: 10px 20px; background: #d1ecf1; border-bottom: 1px solid #bee5eb;
            font-size: 0.9em; color: #0c5460;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 真实 Kimi AI 集成</h1>
            <div class="subtitle">连接到真实的 Kimi AI API 服务</div>
        </div>
        
        <div class="api-status">
            API 状态: {api_status}
        </div>
        
        {"" if self.kimi_ai.has_api_key else '''
        <div class="api-key-info">
            💡 要使用真实的 Kimi AI，请设置环境变量:<br>
            <code>export KIMI_API_KEY=your_kimi_api_key</code><br>
            <code>export KIMI_BASE_URL=https://api.moonshot.cn/v1</code> (可选)
        </div>
        '''}
        
        <div class="model-selector">
            <label for="modelSelect">选择模型:</label>
            <select id="modelSelect" onchange="updateModelInfo()">
                <option value="kimi-k2-turbo-preview">Kimi K2 Turbo Preview</option>
                <option value="ultrathink">UltraThink</option>
            </select>
            <div class="model-info" id="modelInfo">
                快速响应的对话模型
            </div>
        </div>
        
        <div class="demo-buttons">
            <button class="demo-button" onclick="sendDemo('explain')">💭 解释概念</button>
            <button class="demo-button" onclick="sendDemo('creative')">✨ 创意写作</button>
            <button class="demo-button" onclick="sendDemo('analysis')">📊 深度分析</button>
            <button class="demo-button" onclick="sendDemo('code')">💻 编程助手</button>
            <button class="demo-button" onclick="testAPI()">🔧 测试 API</button>
            <button class="demo-button" onclick="clearMessages()">🗑️ 清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    欢迎使用真实 Kimi AI 集成！

{'🟢 您已配置 API Key，可以直接使用真实的 Kimi AI 服务' if self.kimi_ai.has_api_key else '🟡 当前为演示模式，请配置 KIMI_API_KEY 环境变量以使用真实 API'}

支持的模型:
• kimi-k2-turbo-preview: 快速响应
• ultrathink: 深度思考分析
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <textarea 
                id="messageInput" 
                placeholder="输入您的消息，体验真实的 Kimi AI..."
                onkeydown="handleKeyPress(event)"
            ></textarea>
            <button onclick="sendMessage()" id="sendBtn">发送</button>
        </div>
    </div>

    <script>
        const modelDescriptions = {{
            'kimi-k2-turbo-preview': '快速响应的对话模型',
            'ultrathink': '深度思考模型，适合复杂推理任务'
        }};

        function updateModelInfo() {{
            const select = document.getElementById('modelSelect');
            const info = document.getElementById('modelInfo');
            info.textContent = modelDescriptions[select.value];
        }}

        function addMessage(role, content, model = null) {{
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${{role}}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = role === 'user' ? '👤' : role === 'assistant' ? '🤖' : role === 'system' ? 'ℹ️' : '❌';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            if (model) {{
                const badge = document.createElement('span');
                badge.className = 'model-badge';
                badge.textContent = model;
                messageContent.appendChild(badge);
            }}
            
            div.appendChild(avatar);
            div.appendChild(messageContent);
            
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            
            return messageContent;
        }}

        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const modelSelect = document.getElementById('modelSelect');
            const message = input.value.trim();
            
            if (!message) return;
            
            const selectedModel = modelSelect.value;
            
            addMessage('user', message);
            input.value = '';
            
            const assistantMessage = addMessage('assistant', '正在连接 Kimi AI...', selectedModel);
            const sendBtn = document.getElementById('sendBtn');
            const container = document.querySelector('.container');
            
            sendBtn.disabled = true;
            container.classList.add('loading');
            
            try {{
                const response = await fetch('/api/chat', {{
                    method: 'POST',
                    headers: {{ 
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ 
                        message,
                        model: selectedModel,
                        temperature: 0.7,
                        max_tokens: 2000
                    }})
                }});
                
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                
                const data = await response.json();
                
                if (data.success) {{
                    assistantMessage.textContent = data.response;
                }} else {{
                    assistantMessage.className = 'message-content';
                    assistantMessage.parentElement.className = 'message error';
                    assistantMessage.textContent = '❌ 错误: ' + (data.error || '未知错误');
                }}
            }} catch (error) {{
                assistantMessage.className = 'message-content';
                assistantMessage.parentElement.className = 'message error';
                assistantMessage.textContent = '❌ 网络错误: ' + error.message;
            }} finally {{
                sendBtn.disabled = false;
                container.classList.remove('loading');
            }}
        }}

        function sendDemo(type) {{
            const demos = {{
                explain: '请详细解释什么是量子计算',
                creative: '写一个关于未来世界的短故事',
                analysis: '分析人工智能的发展趋势',
                code: '用Python写一个快速排序算法'
            }};
            
            document.getElementById('messageInput').value = demos[type];
            sendMessage();
        }}

        async function testAPI() {{
            addMessage('system', '🔧 测试 Kimi AI API 连接...');
            
            try {{
                const response = await fetch('/api/status');
                if (response.ok) {{
                    const data = await response.json();
                    const status = data.api_configured ? '✅ API 已配置' : '⚠️ API 未配置 (演示模式)';
                    addMessage('system', `API 状态: ${{status}}\\n基础 URL: ${{data.base_url || 'N/A'}}\\n支持的模型: ${{data.models_supported.join(', ')}}`);
                }} else {{
                    addMessage('error', '❌ API 状态检查失败');
                }}
            }} catch (error) {{
                addMessage('error', '❌ 测试失败: ' + error.message);
            }}
        }}

        function clearMessages() {{
            document.getElementById('messages').innerHTML = `
                <div class="message system">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">聊天记录已清空</div>
                </div>
            `;
        }}

        function handleKeyPress(event) {{
            if (event.key === 'Enter' && !event.shiftKey) {{
                event.preventDefault();
                sendMessage();
            }}
        }}

        window.addEventListener('load', () => {{
            updateModelInfo();
        }});
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
            'server_type': 'real_kimi_ai_integration',
            'models_supported': ['kimi-k2-turbo-preview', 'ultrathink'],
            'api_configured': self.kimi_ai.has_api_key,
            'base_url': self.kimi_ai.base_url,
            'demo_mode': not self.kimi_ai.has_api_key
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_models(self):
        """Handle models list request"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        models = [
            {
                "name": "kimi-k2-turbo-preview",
                "description": "Kimi K2 Turbo 预览版 - 快速响应的对话模型",
                "kimi_model": "moonshot-v1-8k",
                "status": "available" if self.kimi_ai.has_api_key else "demo_mode"
            },
            {
                "name": "ultrathink",
                "description": "UltraThink - 深度思考模型，适合复杂推理任务",
                "kimi_model": "moonshot-v1-32k", 
                "status": "available" if self.kimi_ai.has_api_key else "demo_mode"
            }
        ]
        
        response = json.dumps({
            'models': models,
            'api_configured': self.kimi_ai.has_api_key
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_chat(self):
        """Handle chat request with real Kimi AI"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            model = data.get('model', 'kimi-k2-turbo-preview')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 2000)
            
            def process_real_kimi():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self._process_real_kimi(message, model, temperature, max_tokens)
                    )
                finally:
                    loop.close()
            
            success, response_text = process_real_kimi()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': success,
                'response': response_text if success else None,
                'error': None if success else response_text,
                'model': model,
                'api_configured': self.kimi_ai.has_api_key,
                'real_api': self.kimi_ai.has_api_key
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Chat processing error: {str(e)}")
    
    async def _process_real_kimi(self, message, model, temperature, max_tokens):
        """Process chat with real Kimi AI"""
        try:
            # Collect streaming response
            response_parts = []
            async for chunk in self.kimi_ai.chat_with_kimi(message, model, temperature=temperature, max_tokens=max_tokens):
                response_parts.append(chunk)
            
            if response_parts:
                return True, '\\n'.join(response_parts)
            else:
                return False, "收到空响应"
                
        except Exception as e:
            return False, f"Kimi AI 调用失败: {str(e)}"


def run_real_kimi_server():
    """Run the real Kimi AI integration server"""
    PORT = 8091
    
    kimi_ai = RealKimiAI()
    api_status = "已配置" if kimi_ai.has_api_key else "未配置 (演示模式)"
    
    print(f"[Real Kimi AI] Server starting on port {PORT}")
    print(f"[Web] Open http://localhost:{PORT} in your browser")
    print(f"[API] Kimi API Key: {api_status}")
    print(f"[API] Base URL: {kimi_ai.base_url}")
    print(f"[Models] kimi-k2-turbo-preview, ultrathink")
    print(f"[Mode] {'Production (Real API)' if kimi_ai.has_api_key else 'Demo (Mock responses)'}")
    print(f"[Control] Press Ctrl+C to stop")
    
    if not kimi_ai.has_api_key:
        print(f"")
        print(f"[SETUP] To use real Kimi AI, set environment variable:")
        print(f"[SETUP] export KIMI_API_KEY=your_kimi_api_key")
        print(f"[SETUP] export KIMI_BASE_URL=https://api.moonshot.cn/v1  # optional")
    
    with socketserver.TCPServer(("", PORT), RealKimiWebHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\n[STOP] Real Kimi AI server stopped")


if __name__ == "__main__":
    run_real_kimi_server()