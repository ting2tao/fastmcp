import asyncio
from fastmcp import Client

async def main():
    try:
        async with Client("http://localhost:3001/sse") as client:
            print("Connected to server.")
            result = await client.call_tool("add", {"a": 3, "b": 5})
            print(f"3 + 5 = {result}")

            resource = await client.read_resource("greeting://Bob")
            if resource and resource[0]["type"] == "text/plain":
                print(resource[0]["data"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())