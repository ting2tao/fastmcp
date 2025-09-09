from fastmcp import FastMCP

app = FastMCP("example-server", host="127.0.0.1", port=8080)

@app.resource("mcp://example/resource")
async def example_resource():
    return {"name": "Example Resource", "data": "This is example data"}

@app.resource("greeting://Bob")
async def bob_resource():
    return {"name": "Bob Resource", "data": "This is example data"}

@app.tool("example_tool")
async def example_tool(arg1: str):
    return {"message": f"Tool executed with arg1={arg1}"}
@app.tool("add")
async def add(a: int, b: int):
    # 返回原始数值，框架会封装为 TextContent("8")
    return a + b

if __name__ == "__main__":
    # 用 SSE transport 开 HTTP 服务
    app.run("sse")