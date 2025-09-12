"""
Native MCP Protocol Implementation
Implements the Model Context Protocol without FastMCP framework
"""
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class ErrorCode(int, Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass
class MCPError:
    code: ErrorCode
    message: str
    data: Optional[Any] = None


@dataclass
class MCPRequest:
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        if self.id is not None:
            result["id"] = self.id
        return result


@dataclass
class MCPResponse:
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[MCPError] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error is not None:
            result["error"] = {
                "code": self.error.code.value,
                "message": self.error.message
            }
            if self.error.data is not None:
                result["error"]["data"] = self.error.data
        else:
            result["result"] = self.result
        return result


@dataclass
class MCPNotification:
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result


@dataclass
class Tool:
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class Resource:
    uri: str
    name: str
    mimeType: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ResourceContent:
    uri: str
    mimeType: str
    text: Optional[str] = None
    blob: Optional[str] = None


@dataclass
class Prompt:
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None


@dataclass
class ServerCapabilities:
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    experimental: Optional[Dict[str, Any]] = None


@dataclass
class ClientCapabilities:
    sampling: Optional[Dict[str, Any]] = None
    experimental: Optional[Dict[str, Any]] = None


@dataclass
class InitializeParams:
    protocolVersion: str
    capabilities: ClientCapabilities
    clientInfo: Dict[str, Any]


@dataclass
class InitializeResult:
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: Dict[str, Any]


class MCPMessage:
    @staticmethod
    def parse(data: str) -> Union[MCPRequest, MCPResponse, MCPNotification]:
        try:
            obj = json.loads(data)
            
            if "method" in obj:
                if "id" in obj:
                    return MCPRequest(
                        jsonrpc=obj.get("jsonrpc", "2.0"),
                        method=obj["method"],
                        params=obj.get("params"),
                        id=obj["id"]
                    )
                else:
                    return MCPNotification(
                        jsonrpc=obj.get("jsonrpc", "2.0"),
                        method=obj["method"],
                        params=obj.get("params")
                    )
            else:
                return MCPResponse(
                    jsonrpc=obj.get("jsonrpc", "2.0"),
                    id=obj.get("id"),
                    result=obj.get("result"),
                    error=MCPError(
                        code=ErrorCode(obj["error"]["code"]),
                        message=obj["error"]["message"],
                        data=obj["error"].get("data")
                    ) if "error" in obj else None
                )
        except Exception as e:
            raise ValueError(f"Invalid MCP message: {e}")

    @staticmethod
    def serialize(message: Union[MCPRequest, MCPResponse, MCPNotification]) -> str:
        return json.dumps(message.to_dict())