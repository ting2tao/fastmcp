#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Streaming Chat Demo
Demonstrates streaming chat using the actual MCP client
"""
import asyncio
import sys
import os

# 设置控制台编码
if os.name == 'nt':  # Windows
    os.system('chcp 65001')

try:
    from client import MCPClient
    from interactive_client import MCPInteractiveClient
except ImportError:
    sys.path.append('.')
    from client import MCPClient
    from interactive_client import MCPInteractiveClient


class StreamingChatDemo:
    def __init__(self):
        self.client = MCPClient()
        self.connected = False
        
    async def connect(self, host="localhost", port=3001):
        """Connect to MCP server"""
        try:
            await self.client.connect_tcp(host, port)
            init_result = await self.client.initialize("streaming-chat-demo", "1.0.0")
            self.connected = True
            print(f"[OK] Connected! Server: {getattr(init_result, 'serverInfo', {})}")
            return True
        except Exception as e:
            print(f"[FAIL] Connection failed: {e}")
            return False
    
    async def list_tools(self):
        """List available tools"""
        if not self.connected:
            print("Please connect to server first")
            return
        
        try:
            tools = await self.client.list_tools()
            print("\\nAvailable tools:")
            for tool in tools:
                print(f"  * {tool.name}: {tool.description}")
            return tools
        except Exception as e:
            print(f"[FAIL] Failed to get tools: {e}")
            return []
    
    async def demo_streaming_chat(self, message="Hello, please demonstrate streaming chat", response_type="helpful"):
        """Demonstrate streaming chat"""
        if not self.connected:
            print("Please connect to server first")
            return
        
        print(f"\\nUser: {message}")
        print("Assistant: ", end="", flush=True)
        
        try:
            full_response = ""
            async for chunk in self.client.call_tool_streaming('chat_stream', {
                'message': message,
                'response_type': response_type
            }):
                print(chunk + " ", end="", flush=True)
                full_response += chunk + " "
                await asyncio.sleep(0.1)  # Small delay to show streaming effect
            
            print("\\n")
            return full_response
            
        except Exception as e:
            print(f"\\n[FAIL] Streaming chat failed: {e}")
    
    async def demo_chat_history(self):
        """Demonstrate chat history loading"""
        if not self.connected:
            print("Please connect to server first")
            return
        
        print("\\nLoading chat history:")
        
        try:
            async for chunk in self.client.call_tool_streaming('chat_history', {}):
                print(f"  {chunk}")
                await asyncio.sleep(0.2)
                
        except Exception as e:
            print(f"[FAIL] Failed to load history: {e}")
    
    async def interactive_mode(self):
        """Interactive chat mode"""
        print("\\nInteractive mode (type 'quit' to exit, 'history' to view history)")
        print("Use prefixes: /creative, /technical, /helpful")
        
        while True:
            try:
                user_input = input("\\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() in ['history']:
                    await self.demo_chat_history()
                    continue
                elif not user_input:
                    continue
                
                # Check for response type prefix
                response_type = "helpful"
                if user_input.startswith("/creative "):
                    response_type = "creative"
                    user_input = user_input[10:]
                elif user_input.startswith("/technical "):
                    response_type = "technical"
                    user_input = user_input[11:]
                elif user_input.startswith("/helpful "):
                    response_type = "helpful"
                    user_input = user_input[9:]
                
                await self.demo_streaming_chat(user_input, response_type)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\\nGoodbye!")
    
    async def close(self):
        """Close connection"""
        if self.client:
            await self.client.close()


async def main():
    """Main demo function"""
    demo = StreamingChatDemo()
    
    print("MCP Streaming Chat Demo")
    print("=" * 50)
    
    # Connect to server
    print("Connecting to MCP server...")
    if not await demo.connect():
        print("Cannot connect to server. Please ensure MCP server is running")
        return
    
    # List available tools
    await demo.list_tools()
    
    # Demo different response types
    print("\\nDemonstrating different response types:")
    
    # 1. Helpful response
    print("\\n1. Helpful response:")
    await demo.demo_streaming_chat(
        "What is artificial intelligence?", 
        "helpful"
    )
    
    # 2. Creative response
    print("\\n2. Creative response:")
    await demo.demo_streaming_chat(
        "How to make learning more fun?", 
        "creative"
    )
    
    # 3. Technical response
    print("\\n3. Technical response:")
    await demo.demo_streaming_chat(
        "Explain microservices architecture", 
        "technical"
    )
    
    # Demo chat history
    await demo.demo_chat_history()
    
    # Enter interactive mode
    await demo.interactive_mode()
    
    # Cleanup
    await demo.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nDemo ended")
    except Exception as e:
        print(f"\\nRuntime error: {e}")
        import traceback
        traceback.print_exc()