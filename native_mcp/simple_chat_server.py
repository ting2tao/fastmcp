#!/usr/bin/env python3
"""
Simple HTTP Server for MCP Chat Demo
"""
import http.server
import json
import socketserver
from urllib.parse import urlparse

try:
    from client import MCPClient
except ImportError:
    import sys
    sys.path.append('.')
    from client import MCPClient


class MCPChatHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.')
        
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the chat interface
            try:
                with open('chat_interface.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "Chat interface not found")
        
        elif parsed_path.path == '/api/status':
            # Simple status endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({'status': 'running', 'message': 'MCP Chat Server is running'})
            self.wfile.write(response.encode('utf-8'))
        
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/chat':
            # Handle chat requests
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                response_type = data.get('response_type', 'helpful')
                
                # For demo purposes, return a simple response
                # In real implementation, this would connect to MCP server
                demo_response = self.generate_demo_response(message, response_type)
                
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
        else:
            self.send_error(404, "Endpoint not found")
    
    def generate_demo_response(self, message, response_type):
        """Generate a demo response based on message and type"""
        responses = {
            'helpful': f"基于你的问题 '{message[:30]}...'，这里是一个有用的回复。我理解你想要了解这个话题，让我为你详细解释一下相关概念和实际应用场景。",
            'creative': f"🎨 关于 '{message[:30]}...' 这个创意问题，让我们跳出常规思维！我建议从全新的角度来思考这个挑战，结合创新思维和实用方法。",
            'technical': f"📊 对于 '{message[:30]}...' 这个技术问题，让我从架构、实现和最佳实践三个维度来分析。首先是技术架构考虑，然后是具体实现方案。"
        }
        return responses.get(response_type, responses['helpful'])


def run_server():
    """Run the HTTP server"""
    PORT = 8080
    
    with socketserver.TCPServer(("", PORT), MCPChatHandler) as httpd:
        print(f"MCP Chat Demo Server started!")
        print(f"Open http://localhost:{PORT} in your browser")
        print(f"Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer stopped")


if __name__ == "__main__":
    run_server()