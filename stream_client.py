import asyncio
import httpx

BASE_URL = "http://127.0.0.1:3131"

async def list_tools():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/mcp", json={"action": "list_tools"})
        r.raise_for_status()
        return r.json()

async def call_tool(name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/mcp",
            json={"action": "call_tool", "name": name, "arguments": arguments},
        )
        r.raise_for_status()
        return r.json()

async def read_resource(uri: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/mcp", json={"action": "read_resource", "uri": uri})
        r.raise_for_status()
        return r.json()

async def main():
    print("list_tools:", await list_tools())
    print("add(2,3):", await call_tool("add", {"a": 2, "b": 3}))
    print("resource:", await read_resource("mcp://example/resource"))

if __name__ == "__main__":
    asyncio.run(main())
