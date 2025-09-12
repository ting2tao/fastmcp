# Native MCP Protocol Implementation

这是一个使用纯Python实现的原生MCP（Model Context Protocol）客户端和服务端，支持流式传输功能。

## 功能特性

- ✅ 完整的MCP协议支持（JSON-RPC 2.0）
- ✅ 流式工具调用（Streaming tool calls）
- ✅ 支持Tools、Resources和Prompts
- ✅ TCP和stdio传输方式
- ✅ 异步客户端-服务端通信
- ✅ 错误处理和协议合规性

## 文件结构

```
native_mcp/
├── __init__.py          # 包初始化文件
├── protocol.py          # MCP协议核心数据结构
├── server.py           # MCP服务端实现
├── client.py           # MCP客户端实现
├── demo.py             # 完整演示示例
└── test_native_mcp.py  # 基础测试脚本
```

## 快速开始

### 1. 运行交互式演示
```bash
python native_mcp/demo.py
```

### 2. 创建自定义服务器

```python
from native_mcp import MCPServer
import asyncio

server = MCPServer("my-server", "1.0.0")

@server.tool("greet", "Greet someone")
def greet(name: str):
    return f"Hello, {name}!"

@server.tool("stream_data", "Stream some data")
async def stream_data(count: int = 3):
    for i in range(count):
        yield f"Data chunk {i + 1}"
        await asyncio.sleep(0.5)

@server.resource("config://settings", "settings", "application/json")
def get_settings():
    return {"server": "my-server", "version": "1.0.0"}

# 启动TCP服务器
asyncio.run(server.start_tcp("localhost", 3000))
```

### 3. 创建客户端连接

```python
from native_mcp import MCPClient
import asyncio

async def main():
    client = MCPClient()
    
    # 连接到服务器
    await client.connect_tcp("localhost", 3000)
    
    # 初始化连接
    init_result = await client.initialize("my-client", "1.0.0")
    print(f"Connected to: {init_result.serverInfo['name']}")
    
    # 列出可用工具
    tools = await client.list_tools()
    print("Available tools:", [tool.name for tool in tools])
    
    # 调用工具
    result = await client.call_tool("greet", {"name": "World"})
    print("Tool result:", result)
    
    # 流式工具调用
    async for chunk in client.call_tool_streaming("stream_data", {"count": 5}):
        print("Stream chunk:", chunk)
    
    await client.close()

asyncio.run(main())
```

## 运行演示

### 启动服务器（终端1）
```bash
python -c "from native_mcp.demo import run_server; import asyncio; asyncio.run(run_server())"
```

### 连接客户端（终端2）
```bash
python -c "from native_mcp.demo import run_client; import asyncio; asyncio.run(run_client())"
```

## API文档

### MCPServer类

#### 装饰器
- `@server.tool(name, description, input_schema)` - 注册工具
- `@server.resource(uri, name, mime_type, description)` - 注册资源
- `@server.prompt(name, description, arguments)` - 注册提示

#### 方法
- `start_tcp(host, port)` - 启动TCP服务器
- `start_stdio()` - 启动stdio服务器
- `stop()` - 停止服务器

### MCPClient类

#### 连接方法
- `connect_tcp(host, port)` - TCP连接
- `connect_stdio()` - stdio连接

#### MCP操作
- `initialize(client_name, version)` - 初始化连接
- `list_tools()` - 列出工具
- `call_tool(name, arguments)` - 调用工具
- `call_tool_streaming(name, arguments)` - 流式工具调用
- `list_resources()` - 列出资源
- `read_resource(uri)` - 读取资源
- `list_prompts()` - 列出提示
- `get_prompt(name, arguments)` - 获取提示

## 测试

运行基础测试：
```bash
python native_mcp/test_native_mcp.py
```

## 协议支持

支持MCP协议规范中的以下功能：

- JSON-RPC 2.0消息格式
- 初始化握手
- 工具调用和流式响应
- 资源读取
- 提示获取
- 错误处理
- ping/pong心跳

## 注意事项

1. 这是一个教育和演示用途的实现，生产环境请使用官方的FastMCP框架
2. 流式传输通过notification实现，需要客户端和服务端都支持
3. stdio传输在Windows上可能需要特殊处理

## 许可证

本实现仅供学习和演示使用。