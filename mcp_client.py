import requests
import json

class MCPClient:
    def __init__(self, server_url):
        """
        初始化 MCP 客户端

        :param server_url: MCP 服务器的 URL，例如 "http://localhost:8000/mcp"
        """
        self.server_url = server_url

    def send_request(self, method, params=None):
        """
        向 MCP 服务器发送 JSON-RPC 请求

        :param method: 要调用的方法名
        :param params: 方法参数，默认为 None
        :return: 服务器返回的结果
        """
        request_body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }

        try:
            response = requests.post(self.server_url, json=request_body)
            response.raise_for_status()
            response_data = response.json()

            if "result" in response_data:
                return response_data["result"]
            elif "error" in response_data:
                raise Exception(f"JSON-RPC Error: {response_data['error']}")
            else:
                raise Exception("Invalid JSON-RPC response")
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP Request failed: {e}")

    def list_resources(self):
        """
        列出 MCP 服务器上可用的资源

        :return: 资源列表
        """
        return self.send_request("list_resources")

    def get_resource(self, resource_id):
        """
        获取指定 ID 的资源

        :param resource_id: 资源的 ID
        :return: 资源内容
        """
        return self.send_request("get_resource", {"id": resource_id})

    def call_tool(self, tool_name, args):
        """
        调用 MCP 服务器上的工具

        :param tool_name: 工具名称
        :param args: 工具参数，字典形式
        :return: 工具执行结果
        """
        return self.send_request("call_tool", {"tool": tool_name, "args": args})

if __name__ == "__main__":
    client = MCPClient("http://localhost:8080/mcp")
    try:
        resources = client.list_resources()
        print("Resources:", resources)
        resource = client.get_resource("example_resource")
        print("Resource:", resource)
        result = client.call_tool("example_tool", {"arg1": "value1"})
        print("Tool result:", result)
    except Exception as e:
        print(f"Error: {e}")