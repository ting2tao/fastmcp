#!/usr/bin/env python3
"""
Minimal test to verify server startup
"""
import asyncio

print("Starting minimal test...")

async def minimal_server_test():
    print("Async function started")
    server = await asyncio.start_server(
        lambda r, w: None, "localhost", 3003
    )
    print("Server created on port 3003")
    
    async with server:
        print("Server is serving...")
        # Don't serve forever for this test
        await asyncio.sleep(1)
        print("Test completed")

if __name__ == "__main__":
    print("About to run asyncio.run")
    asyncio.run(minimal_server_test())
    print("Test finished")