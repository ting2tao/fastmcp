from fastmcp import FastMCP

mcp = FastMCP("MyServer")


@mcp.tool(name="add")  # 显式命名工具，避免依赖函数名
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> list:
    """Get a personalized greeting"""
    # 返回符合规范的资源结构，包含类型和数据
    return [{
        "type": "text/plain",
        "data": f"Hello, {name}!",
        "metadata": {"language": "en"}  # 可选扩展字段
    }]


if __name__ == "__main__":
    # 安全获取已注册工具名称（避免访问私有属性）

    print(f"Starting server with tools: {mcp.get_tools()}")

    # 使用HTTP传输并显式绑定端口
    mcp.run(transport='sse')