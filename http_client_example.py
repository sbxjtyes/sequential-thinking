#!/usr/bin/env python
"""
HTTP客户端调用示例 | HTTP Client Example

演示如何从本地电脑调用部署在云服务器上的MCP服务。
Demonstrates how to call MCP server deployed on a remote cloud server.

使用前请确保：
1. 云服务器上的MCP服务已启动并监听HTTP端口
2. 网络可达（防火墙已开放相应端口）
3. 已安装mcp库：pip install mcp
"""

import asyncio
import json
from typing import Optional

# MCP客户端库
try:
    from mcp import ClientSession
    from mcp.client.streamablehttp import streamablehttp_client
except ImportError:
    print("请先安装mcp库: pip install mcp")
    print("Please install mcp library: pip install mcp")
    exit(1)


class SequentialThinkingClient:
    """
    Sequential Thinking MCP HTTP客户端 | HTTP Client for Sequential Thinking MCP.
    
    用于远程调用部署在云服务器上的MCP服务。
    Used for remote calls to MCP server deployed on cloud server.
    """
    
    def __init__(self, server_url: str):
        """
        初始化客户端 | Initialize the client.
        
        Args:
            server_url: MCP服务器地址，例如 "http://your-server:8000/mcp"
                       | MCP server URL, e.g., "http://your-server:8000/mcp"
        """
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
    
    async def connect(self):
        """
        连接到MCP服务器 | Connect to MCP server.
        """
        print(f"正在连接到MCP服务器: {self.server_url}")
        
        # 创建HTTP客户端连接
        self._client = streamablehttp_client(self.server_url)
        self._read, self._write, self._session_info = await self._client.__aenter__()
        
        # 创建会话
        self.session = ClientSession(self._read, self._write)
        await self.session.__aenter__()
        
        # 初始化连接
        result = await self.session.initialize()
        print(f"已连接，服务器信息: {result.serverInfo.name} v{result.serverInfo.version}")
        
        # 列出可用工具
        tools = await self.session.list_tools()
        print(f"\n可用工具 | Available tools ({len(tools.tools)}):")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
    
    async def disconnect(self):
        """
        断开连接 | Disconnect from server.
        """
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, '_client'):
            await self._client.__aexit__(None, None, None)
        print("已断开连接")
    
    async def process_thought(
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
        处理单个思考节点 | Process a single thought.
        
        Args:
            thought: 思考内容 | Thought content
            thought_number: 当前思考序号 | Current thought number
            total_thoughts: 总思考数 | Total thoughts planned
            next_thought_needed: 是否需要后续思考 | Whether more thoughts needed
            thought_type: 思考类型 | Thought type
            stage: 思考阶段 | Thinking stage
            **kwargs: 其他可选参数 | Other optional parameters
        
        Returns:
            分析结果字典 | Analysis result dictionary
        """
        if not self.session:
            raise RuntimeError("未连接到服务器，请先调用connect()")
        
        # 构建参数
        arguments = {
            "thought": thought,
            "thought_number": thought_number,
            "total_thoughts": total_thoughts,
            "next_thought_needed": next_thought_needed,
            "thought_type": thought_type,
            "stage": stage,
            **kwargs
        }
        
        # 调用工具
        result = await self.session.call_tool("process_thought", arguments)
        
        # 解析结果
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                return json.loads(content.text)
        
        return {"error": "No response content", "status": "failed"}
    
    async def generate_summary(self) -> dict:
        """
        生成思考过程摘要 | Generate thinking process summary.
        """
        if not self.session:
            raise RuntimeError("未连接到服务器，请先调用connect()")
        
        result = await self.session.call_tool("generate_summary", {})
        
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                return json.loads(content.text)
        
        return {"error": "No response content", "status": "failed"}
    
    async def clear_history(self) -> dict:
        """
        清除思考历史 | Clear thought history.
        """
        if not self.session:
            raise RuntimeError("未连接到服务器，请先调用connect()")
        
        result = await self.session.call_tool("clear_history", {})
        
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                return json.loads(content.text)
        
        return {"error": "No response content", "status": "failed"}


async def demo():
    """
    演示如何使用HTTP客户端调用MCP服务 | Demo how to use HTTP client.
    """
    # 配置服务器地址（修改为你的云服务器地址）
    # Configure server URL (change to your cloud server address)
    SERVER_URL = "http://YOUR_CLOUD_SERVER_IP:8000/mcp"
    
    print("=" * 60)
    print("Sequential Thinking MCP - HTTP客户端示例")
    print("Sequential Thinking MCP - HTTP Client Example")
    print("=" * 60)
    print(f"\n目标服务器 | Target Server: {SERVER_URL}")
    print("\n请修改 SERVER_URL 为你的云服务器地址")
    print("Please modify SERVER_URL to your cloud server address\n")
    
    # 创建客户端
    client = SequentialThinkingClient(SERVER_URL)
    
    try:
        # 连接服务器
        await client.connect()
        
        # 示例：处理思考
        print("\n" + "=" * 40)
        print("示例1：处理思考 | Example 1: Process Thought")
        print("=" * 40)
        
        result = await client.process_thought(
            thought="我需要分析如何通过HTTP远程调用MCP服务。首先考虑网络连接问题。",
            thought_number=1,
            total_thoughts=3,
            thought_type="analysis",
            stage="Problem Definition",
            lang="zh"
        )
        print(f"\n思考分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 继续思考
        print("\n" + "=" * 40)
        print("示例2：继续思考 | Example 2: Continue Thinking")
        print("=" * 40)
        
        result = await client.process_thought(
            thought="HTTP传输模式需要服务器监听0.0.0.0地址，并开放防火墙端口。",
            thought_number=2,
            total_thoughts=3,
            thought_type="hypothesis",
            stage="Analysis",
            lang="zh"
        )
        print(f"\n思考分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 生成摘要
        print("\n" + "=" * 40)
        print("示例3：生成摘要 | Example 3: Generate Summary")
        print("=" * 40)
        
        summary = await client.generate_summary()
        print(f"\n思考过程摘要:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n错误 | Error: {e}")
        print("\n请检查：")
        print("1. 服务器地址是否正确")
        print("2. 服务器是否已启动")
        print("3. 网络是否可达")
        print("4. 防火墙端口是否开放")
    
    finally:
        # 断开连接
        await client.disconnect()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())
