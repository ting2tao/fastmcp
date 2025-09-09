from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn
import pydantic_core


# 独立的 Streamable HTTP 服务器（同时保留 SSE 路由）
mcp = FastMCP("streamable-server", host="127.0.0.1", port=3131)


@mcp.tool("add")
async def add(a: int, b: int):
    # 返回原始数值，框架会封装为 TextContent("<num>")
    return a + b


@mcp.resource("mcp://example/resource")
async def example_resource():
    return {"name": "Example Resource", "data": "This is example data"}


def build_app():
    # 仅提供 /mcp 的 HTTP 接口（不包含 SSE）
    async def mcp_handler(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid json"}, status_code=400)

        action = payload.get("action")
        if action == "list_tools":
            tools = await mcp.get_tools()
            return JSONResponse(
                {
                    "tools": [
                        {"name": name, "description": tool.description}
                        for name, tool in tools.items()
                    ]
                }
            )
        elif action == "call_tool":
            name = payload.get("name")
            arguments = payload.get("arguments") or {}
            try:
                content = await mcp._mcp_call_tool(name, arguments)  # type: ignore[attr-defined]
                serializable = pydantic_core.to_jsonable_python(content)
                return JSONResponse({"ok": True, "content": serializable})
            except Exception as e:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
        elif action == "read_resource":
            uri = payload.get("uri")
            if not uri:
                return JSONResponse({"error": "uri is required"}, status_code=400)
            try:
                content = await mcp._mcp_read_resource(uri)  # type: ignore[attr-defined]
                serializable = pydantic_core.to_jsonable_python(content)
                return JSONResponse({"ok": True, "content": serializable})
            except Exception as e:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
        else:
            return JSONResponse({"error": "unknown action"}, status_code=400)

    return Starlette(routes=[Route("/mcp", mcp_handler, methods=["POST"])])



if __name__ == "__main__":
    # 仅运行 /mcp（端口统一为 3131）
    uvicorn.run(build_app(), host="127.0.0.1", port=3131)


