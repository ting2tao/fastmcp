#!/usr/bin/env python3
"""
Enhanced Simple Kimi AI Integration with .env support
Supports both environment variables and .env file
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


def load_env_file(env_path='.env'):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and not os.getenv(key):  # Only set if not already in environment
                        os.environ[key] = value
        print(f"[ENV] 已加载 .env 文件: {env_path}")
    except Exception as e:
        print(f"[ENV] 加载 .env 文件失败: {e}")


class EnhancedKimiAI:
    """Enhanced Kimi AI client with .env support"""
    
    def __init__(self):
        # Load .env file first
        load_env_file('.env')
        
        self.api_key = os.getenv('KIMI_API_KEY', '')
        self.base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        self.has_key = bool(self.api_key)
        
        print(f"[Kimi AI] API Key: {'已配置' if self.has_key else '未配置'}")
        print(f"[Kimi AI] Base URL: {self.base_url}")
        
        if self.has_key:
            masked_key = self.api_key[:8] + '*' * (len(self.api_key) - 12) + self.api_key[-4:] if len(self.api_key) > 12 else self.api_key[:4] + '*' * (len(self.api_key) - 4)
            print(f"[Kimi AI] API Key (masked): {masked_key}")

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
                    return f"[{model.upper()} - 真实 API] \n{content}"
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

演示模式说明: 请配置 .env 文件或设置 KIMI_API_KEY 环境变量使用真实 API"""
        else:
            return f"""[KIMI K2 TURBO - 演示模式]

处理您的消息: {message[:50]}...

关于您的问题: {message[:40]}

这是演示响应，展示:
1. 快速响应特点
2. 智能对话能力  
3. 多轮交互支持

演示模式说明: 请配置 .env 文件或设置 KIMI_API_KEY 环境变量使用真实 API"""


class EnhancedKimiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.kimi = EnhancedKimiAI()
        super().__init__(*args, directory='.')
    
    def do_GET(self):
        if self.path == '/':
            self.serve_page()
        elif self.path == '/api/status':
            self.serve_status()
        elif self.path == '/api/env-example':
            self.serve_env_example()
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
        
        env_status = "✅ 已加载" if os.path.exists('.env') else "❌ 未找到"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kimi AI 集成 (支持 .env)</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
        .container {{ max-width: 800px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
        .status {{ padding: 10px 20px; background: {color}; color: white; text-align: center; font-weight: 600; }}
        .env-info {{ padding: 10px 20px; background: #e3f2fd; border-bottom: 1px solid #bbdefb; font-size: 0.9em; }}
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
        .config-section {{ padding: 15px 20px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 10px 20px; border-radius: 4px; }}
        .code {{ background: #f8f9fa; padding: 8px 12px; border-radius: 4px; font-family: monospace; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Kimi AI 集成</h1>
            <p>支持 .env 文件和环境变量配置</p>
        </div>
        
        <div class="status">API 状态: {status}</div>
        
        <div class="env-info">
            📄 .env 文件状态: {env_status} | 
            🔧 Base URL: {self.kimi.base_url} | 
            📡 配置来源: {'环境变量/.env' if self.kimi.has_key else '.env 文件未配置或为空'}
        </div>
        
        {"" if self.kimi.has_key else f'''
        <div class="config-section">
            <h4>⚙️ 配置说明</h4>
            <p><strong>方法1: 创建 .env 文件</strong> (推荐)</p>
            <div class="code">KIMI_API_KEY=your_kimi_api_key<br>KIMI_BASE_URL=https://api.moonshot.cn/v1</div>
            
            <p><strong>方法2: 设置环境变量</strong></p>
            <div class="code">export KIMI_API_KEY=your_kimi_api_key</div>
            
            <p>💡 <a href="/api/env-example" target="_blank">点击查看 .env 文件示例</a></p>
        </div>
        '''}
        
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
            <button class="demo-btn" onclick="demo('分析当前科技发展趋势')">深度分析</button>
            <button class="demo-btn" onclick="clearChat()">清空</button>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-content">欢迎使用 Kimi AI 集成！
                
{f'🟢 已配置 API Key，正在使用真实 Kimi AI 服务' if self.kimi.has_key else '🟡 演示模式：请配置 .env 文件或设置 KIMI_API_KEY 环境变量'}

支持模型:
• kimi-k2-turbo-preview (快速响应)
• ultrathink (深度思考)

配置方式:
• 创建 .env 文件 (推荐)
• 设置环境变量</div>
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
            'models': ['kimi-k2-turbo-preview', 'ultrathink'],
            'env_file_exists': os.path.exists('.env'),
            'config_source': 'env_or_dotenv' if self.kimi.has_key else 'not_configured'
        })
        self.wfile.write(response.encode('utf-8'))
    
    def serve_env_example(self):
        """Serve .env file example"""
        env_example = '''# Kimi AI MCP 服务器配置
# 请将您的 Kimi API Key 设置到这个文件中

# 必需配置
KIMI_API_KEY=your_actual_api_key_here

# 可选配置 (默认值如下)
KIMI_BASE_URL=https://api.moonshot.cn/v1

# 支持的模型：
# - kimi-k2-turbo-preview: 快速响应的对话模型 (对应 moonshot-v1-8k)
# - ultrathink: 深度思考模型，适合复杂推理任务 (对应 moonshot-v1-32k)

# 使用说明：
# 1. 将此文件保存为 .env
# 2. 替换 your_actual_api_key_here 为您的真实 API Key
# 3. 重启服务器即可生效

# 注意：
# - .env 文件不应该提交到版本控制系统
# - 请妥善保管您的 API Key
# - 如果同时设置了环境变量，环境变量优先级更高'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename=".env.example"')
        self.end_headers()
        self.wfile.write(env_example.encode('utf-8'))
    
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
                'api_used': self.kimi.has_key,
                'config_source': 'env_or_dotenv' if self.kimi.has_key else 'not_configured'
            })
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"处理错误: {str(e)}")


def main():
    PORT = 8092
    print(f"[Kimi AI] 增强版集成服务器启动: http://localhost:{PORT}")
    print(f"[配置] 支持 .env 文件和环境变量")
    
    # Load and display config
    load_env_file('.env')
    has_key = bool(os.getenv('KIMI_API_KEY'))
    
    print(f"[配置] .env 文件: {'存在' if os.path.exists('.env') else '不存在'}")
    print(f"[配置] KIMI_API_KEY: {'已设置' if has_key else '未设置'}")
    print(f"[配置] KIMI_BASE_URL: {os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')}")
    print(f"[使用] 在浏览器中打开 http://localhost:{PORT}")
    print(f"[停止] 按 Ctrl+C 停止服务器")
    
    if not has_key:
        print(f"")
        print(f"[提示] 要使用真实 Kimi AI，请:")
        print(f"[提示] 1. 创建 .env 文件，添加: KIMI_API_KEY=your_key")
        print(f"[提示] 2. 或设置环境变量: export KIMI_API_KEY=your_key")
    
    try:
        with socketserver.TCPServer(("", PORT), EnhancedKimiHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n[停止] 服务器已停止")

if __name__ == "__main__":
    main()