#!/usr/bin/env python3
"""
Simplified Real Kimi AI Integration Server
Direct HTTP calls to Kimi API without complex dependencies
"""
import asyncio
import json
import http.server
import socketserver
from urllib.parse import urlparse
import urllib.request
import urllib.error
import os
import ssl

class SimpleKimiAI:
    """Simple Kimi AI client using urllib"""
    
    def __init__(self):
        self.api_key = os.getenv('KIMI_API_KEY', '')
        self.base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        self.has_key = bool(self.api_key)
        print(f"[Kimi AI] API Key: {'已配置' if self.has_key else '未配置'}")
        print(f"[Kimi AI] Base URL: {self.base_url}")

    async def chat(self, message: str, model: str = "kimi-k2-turbo-preview"):
        """Chat with Kimi AI or fallback to demo"""
        if not self.has_key:
            return await self._demo_chat(message, model)
        
        try:
            return await self._real_chat(message, model)
        except Exception as e:
            print(f"[ERROR] Kimi API失败: {e}")
            return await self._demo_chat(message, model)
    
    async def _real_chat(self, message: str, model: str):
        """Call real Kimi API"""
        model_map = {
            'kimi-k2-turbo-preview': 'moonshot-v1-8k',
            'ultrathink': 'moonshot-v1-32k'
        }
        kimi_model = model_map.get(model, 'moonshot-v1-8k')
        
        url = f"{self.base_url}/chat/completions"
        data = {
            "model": kimi_model,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return f"[{model.upper()} - 真实 API] \\n{content}"
                else:
                    return f"[{model.upper()}] API 返回格式异常"
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"[ERROR] Kimi API HTTP错误 {e.code}: {error_body}"
        except Exception as e:
            return f"[ERROR] Kimi API 调用失败: {str(e)}"
    
    async def _demo_chat(self, message: str, model: str):
        """Demo fallback response"""
        if model == "ultrathink":
            return f"""[ULTRATHINK - 演示模式]

深度分析您的问题: {message[:50]}...

第一层思考: 问题本质
{message[:100]}

第二层思考: 概念框架  
需要多角度分析这个问题

第三层思考: 深层含义
基于深度分析的综合观点

演示模式说明: 请设置 KIMI_API_KEY 环境变量使用真实 API"""
        else:
            return f"""[KIMI K2 TURBO - 演示模式]

处理您的消息: {message[:50]}...

关于您的问题: {message[:40]}

这是演示响应，展示:
1. 快速响应特点
2. 智能对话能力  
3. 多轮交互支持

演示模式说明: 请设置 KIMI_API_KEY 环境变量使用真实 API"""


class SimpleKimiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.kimi = SimpleKimiAI()
        super().__init__(*args, directory='.')
    
    def do_GET(self):
        if self.path == '/':
            self.serve_page()
        elif self.path == '/api/status':
            self.serve_status()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/chat':
            self.handle_chat()
        else:
            self.send_error(404)
    
    def serve_page(self):
        status = "已配置 API Key" if self.kimi.has_key else "未配置 API Key (演示模式)"
        color = "#28a745" if self.kimi.has_key else "#ffc107"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kimi AI 真实集成</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
        .container {{ max-width: 800px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
        .status {{ padding: 10px 20px; background: {color}; color: white; text-align: center; font-weight: 600; }}
        .models {{ padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; }}
        .model-select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; margin-right: 10px; }}
        .messages {{ height: 400px; overflow-y: auto; padding: 20px; }}
        .message {{ margin-bottom: 15px; display: flex; gap: 10px; }}
        .message.user {{ justify-content: flex-end; }}
        .message-content {{ max-width: 70%; padding: 10px 15px; border-radius: 18px; line-height: 1.4; white-space: pre-line; }}
        .message.user .message-content {{ background: #007bff; color: white; }}
        .message.assistant .message-content {{ background: #f1f3f4; color: #333; }}
        .message.system .message-content {{ background: #e3f2fd; color: #1976d2; }}
        .input-area {{ padding: 20px; border-top: 1px solid #e9ecef; display: flex; gap: 10px; }}
        .input-area textarea {{ flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; resize: none; font-family: inherit; }}
        .input-area button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 20px; cursor: pointer; }}
        .input-area button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .demos {{ padding: 10px 20px; background: #f8f9fa; text-align: center; }}
        .demo-btn {{ margin: 5px; padding: 5px 10px; background: white; border: 1px solid #ddd; border-radius: 15px; cursor: pointer; font-size: 0.9em; }}
        .demo-btn:hover {{ background: #e9ecef; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Kimi AI 真实集成</h1>
            <p>连接到真实的 Kimi AI API</p>
        </div>
        
        <div class="status">API 状态: {status}</div>
        
        <div class="models">
            <label>选择模型:</label>
            <select id="model" class="model-select">
                <option value="kimi-k2-turbo-preview">Kimi K2 Turbo</option>
                <option value="ultrathink">UltraThink</option>
            </select>
            <span id="modelInfo">快速响应模型</span>
        </div>
        
        <div class="demos">
            <button class="demo-btn" onclick="demo('你好，请介绍一下你自己')">自我介绍</button>
            <button class="demo-btn" onclick="demo('解释一下人工智能')">解释AI</button>
            <button class="demo-btn" onclick="demo('写一个Python排序算法')">编程帮助</button>
            <button class="demo-btn" onclick="clearChat()">清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-content">欢迎使用 Kimi AI 真实集成！
                
{'🟢 已配置 API Key，正在使用真实 Kimi AI 服务' if self.kimi.has_key else '🟡 演示模式：请设置 KIMI_API_KEY 环境变量'}

支持模型:
• kimi-k2-turbo-preview (快速响应)
• ultrathink (深度思考)</div>
            </div>
        </div>
        
        <div class="input-area">
            <textarea id="input" placeholder="输入消息..." rows="2" onkeypress="onEnter(event)"></textarea>
            <button onclick="sendMessage()" id="sendBtn">发送</button>
        </div>
    </div>

    <script>
        const models = {{
            'kimi-k2-turbo-preview': '快速响应模型',
            'ultrathink': '深度思考模型'
        }};
        
        document.getElementById('model').onchange = function() {{
            document.getElementById('modelInfo').textContent = models[this.value];
        }};
        
        function addMessage(role, content) {{
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${{role}}`;
            div.innerHTML = `<div class="message-content">${{content}}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return div.querySelector('.message-content');
        }}
        
        async function sendMessage() {{
            const input = document.getElementById('input');
            const model = document.getElementById('model').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            const assistantMsg = addMessage('assistant', '正在连接 Kimi AI...');
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            
            try {{
                const response = await fetch('/api/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message, model}})
                }});
                
                const data = await response.json();
                assistantMsg.textContent = data.response || data.error || '未知错误';
            }} catch (error) {{
                assistantMsg.textContent = '网络错误: ' + error.message;
            }} finally {{
                sendBtn.disabled = false;
            }}
        }}
        
        function demo(text) {{
            document.getElementById('input').value = text;
            sendMessage();
        }}
        
        function clearChat() {{
            document.getElementById('messages').innerHTML = `
                <div class="message system">
                    <div class="message-content">聊天记录已清空</div>
                </div>
            `;
        }}
        
        function onEnter(event) {{
            if (event.key === 'Enter' && !event.shiftKey) {{
                event.preventDefault();
                sendMessage();
            }}
        }}
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_status(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps({
            'status': 'running',
            'api_configured': self.kimi.has_key,
            'base_url': self.kimi.base_url,
            'models': ['kimi-k2-turbo-preview', 'ultrathink']
        })
        self.wfile.write(response.encode('utf-8'))
    
    def handle_chat(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            model = data.get('model', 'kimi-k2-turbo-preview')
            
            # Process chat
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response_text = loop.run_until_complete(self.kimi.chat(message, model))
            finally:
                loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                'success': True,
                'response': response_text,
                'model': model,
                'api_used': self.kimi.has_key
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"处理错误: {str(e)}")


def main():
    PORT = 8090
    print(f"[Kimi AI] 真实集成服务器启动: http://localhost:{PORT}")
    print(f"[环境] KIMI_API_KEY: {'已设置' if os.getenv('KIMI_API_KEY') else '未设置'}")
    print(f"[环境] KIMI_BASE_URL: {os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')}")
    print(f"[使用] 在浏览器中打开 http://localhost:{PORT}")
    print(f"[停止] 按 Ctrl+C 停止服务器")
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleKimiHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n[停止] 服务器已停止")

if __name__ == "__main__":
    main()