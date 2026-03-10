#!/usr/bin/env python
"""
简单HTTP客户端 - 无需mcp库 | Simple HTTP Client - No mcp library required

使用标准库和requests直接调用MCP服务。
Uses standard library and requests to call MCP service directly.
"""

import json
import requests
from typing import Optional


class SimpleMCPClient:
    """
    简单MCP HTTP客户端 | Simple MCP HTTP Client.
    
    不依赖mcp库，直接通过HTTP调用。
    No mcp library dependency, calls via HTTP directly.
    """
    
    def __init__(self, server_url: str):
        """
        初始化客户端 | Initialize client.
        
        Args:
            server_url: MCP服务器地址，例如 "http://192.168.1.100:8000/mcp"
        """
        self.server_url = server_url.rstrip('/')
        self.request_id = 0
    
    def _get_next_id(self) -> int:
        """获取下一个请求ID | Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    def _call(self, method: str, params: dict = None) -> dict:
        """
        发送JSON-RPC请求 | Send JSON-RPC request.
        
        Args:
            method: MCP方法名 | MCP method name
            params: 参数字典 | Parameters dict
        
        Returns:
            响应结果 | Response result
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(
            self.server_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")
        
        return result.get("result", {})
    
    def initialize(self) -> dict:
        """
        初始化连接 | Initialize connection.
        """
        return self._call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "simple-http-client",
                "version": "1.0.0"
            }
        })
    
    def list_tools(self) -> list:
        """
        列出可用工具 | List available tools.
        """
        result = self._call("tools/list")
        return result.get("tools", [])
    
    def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """
        调用工具 | Call a tool.
        
        Args:
            tool_name: 工具名称 | Tool name
            arguments: 工具参数 | Tool arguments
        
        Returns:
            工具执行结果 | Tool execution result
        """
        result = self._call("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        # 解析返回内容 | Parse return content
        content = result.get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "{}")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
        
        return result
    
    def process_thought(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool = True,
        thought_type: str = "analysis",
        stage: str = "Problem Definition",
        **kwargs
    ) -> dict:
        """
        处理思考 | Process a thought.
        """
        arguments = {
            "thought": thought,
            "thought_number": thought_number,
            "total_thoughts": total_thoughts,
            "next_thought_needed": next_thought_needed,
            "thought_type": thought_type,
            "stage": stage,
            **kwargs
        }
        return self.call_tool("process_thought", arguments)
    
    def generate_summary(self) -> dict:
        """
        生成摘要 | Generate summary.
        """
        return self.call_tool("generate_summary")
    
    def clear_history(self) -> dict:
        """
        清除历史 | Clear history.
        """
        return self.call_tool("clear_history")


def main():
    """
    使用示例 | Usage example.
    """
    # 修改为你的云服务器地址 | Change to your cloud server address
    SERVER_URL = "http://YOUR_CLOUD_SERVER_IP:8000/mcp"
    
    print("=" * 60)
    print("Sequential Thinking MCP - 简单HTTP客户端")
    print("=" * 60)
    print(f"\n服务器地址: {SERVER_URL}")
    print("请修改 SERVER_URL 为你的云服务器地址\n")
    
    # 创建客户端
    client = SimpleMCPClient(SERVER_URL)
    
    try:
        # 初始化
        print("正在连接...")
        info = client.initialize()
        print(f"已连接: {info.get('serverInfo', {}).get('name', 'Unknown')}")
        
        # 列出工具
        print("\n可用工具:")
        tools = client.list_tools()
        for tool in tools:
            print(f"  - {tool.get('name')}")
        
        # 处理思考
        print("\n" + "-" * 40)
        print("示例: 处理思考")
        result = client.process_thought(
            thought="这是一个测试思考，验证HTTP远程调用是否正常工作。",
            thought_number=1,
            total_thoughts=1,
            next_thought_needed=False,
            lang="zh"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except requests.exceptions.ConnectionError:
        print("\n连接失败！请检查:")
        print("1. 服务器地址是否正确")
        print("2. 服务器是否已启动")
        print("3. 防火墙端口是否开放")
    except Exception as e:
        print(f"\n错误: {e}")
    
    print("\n完成")


if __name__ == "__main__":
    main()
