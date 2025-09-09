import asyncio
import traceback
from fastmcp import Client
from mcp.types import TextContent

async def main():
    try:
        async with Client("http://127.0.0.1:8080/sse") as client:
            print("Connected to server.")

            try:
                tools = await client.list_tools()
                print("Tools:", [t.name for t in tools])
            except Exception:
                print("Error during list_tools:")
                traceback.print_exc()

            try:
                result = await client.call_tool("add", {"a": 3, "b": 5})
                if isinstance(result[0], TextContent):
                    text = result[0].text
                    try:
                        value = int(text)
                    except ValueError:
                        import json
                        value = json.loads(text)
                        if isinstance(value, list) and value and isinstance(value[0], dict) and "text" in value[0]:
                            value = int(value[0]["text"])  # 兜底兼容
                    print(f"3 + 5 = {value}")
                else:
                    print("3 + 5 (raw) =", result)
            except Exception:
                print("Error during call_tool('add'):")
                traceback.print_exc()

            # 可选：如需调试资源再开启
            try:
                resource = await client.read_resource("mcp://example/resource")
                print("resource:", resource)
            except Exception:
                print("Error during read_resource:")
                traceback.print_exc()

            # 可选：如需调试资源再开启
            try:
                resource = await client.read_resource("greeting://Bob")
                print("resource:", resource)
            except Exception:
                print("Error during read_resource:")
                traceback.print_exc()
    except Exception:
        print("Top-level error:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

    