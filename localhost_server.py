from fastmcp import FastMCP

# 创建 MCP server
server = FastMCP("local-demo")

# 注册工具
@server.tool()
def say_hello(name: str) -> str:
    """返回一个打招呼的消息"""
    return f"Hello, {name}! 欢迎使用 FastMCP 2.2.0 🚀"

if __name__ == "__main__":
    server.run()
