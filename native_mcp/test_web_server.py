#!/usr/bin/env python3
"""
Test script to verify the improved web server
"""
import asyncio
import json
import requests
import time

def test_web_server():
    """Test the improved web server"""
    base_url = "http://localhost:8083"
    
    print("Testing improved MCP web server...")
    
    try:
        # Test 1: Check server is running
        print("\\n1. Testing server status...")
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"Status response: {response.json()}")
        
        # Test 2: Try to connect to MCP
        print("\\n2. Testing MCP connection...")
        response = requests.get(f"{base_url}/api/connect", timeout=10)
        connect_result = response.json()
        print(f"Connect response: {connect_result}")
        
        if connect_result.get('success'):
            print("✅ MCP connection successful!")
            
            # Test 3: Send a test message
            print("\\n3. Testing chat message...")
            chat_data = {
                "message": "Hello, this is a test message",
                "response_type": "helpful"
            }
            
            response = requests.post(
                f"{base_url}/api/chat", 
                json=chat_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            chat_result = response.json()
            print(f"Chat response: {chat_result}")
            
            if chat_result.get('success'):
                print("✅ Chat test successful!")
                print(f"Response: {chat_result.get('response', '')[:100]}...")
            else:
                print(f"❌ Chat test failed: {chat_result}")
        else:
            print(f"❌ MCP connection failed: {connect_result}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    test_web_server()