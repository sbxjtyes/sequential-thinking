#!/usr/bin/env python
"""
简单的MCP服务器连接测试
Simple MCP server connection test
"""

import requests
import json

# 服务器地址
SERVER_URL = "http://106.54.55.203:8000"

print("=" * 60)
print("MCP服务器连接测试 | MCP Server Connection Test")
print("=" * 60)

# 测试1: 健康检查
print("\n1. 测试健康检查端点 | Testing health endpoint...")
try:
    response = requests.get(f"{SERVER_URL}/health", timeout=5)
    print(f"   状态码 | Status: {response.status_code}")
    print(f"   响应 | Response: {response.text}")
except Exception as e:
    print(f"   错误 | Error: {e}")

# 测试2: 尝试MCP调用（根路径）
print("\n2. 测试MCP端点（根路径）| Testing MCP endpoint (root)...")
try:
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    response = requests.post(
        SERVER_URL,
        json=mcp_request,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   状态码 | Status: {response.status_code}")
    print(f"   响应 | Response: {response.text[:200]}...")
except Exception as e:
    print(f"   错误 | Error: {e}")

# 测试3: 尝试MCP调用（/mcp路径）
print("\n3. 测试MCP端点（/mcp路径）| Testing MCP endpoint (/mcp)...")
try:
    response = requests.post(
        f"{SERVER_URL}/mcp",
        json=mcp_request,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   状态码 | Status: {response.status_code}")
    print(f"   响应 | Response: {response.text[:200]}...")
except Exception as e:
    print(f"   错误 | Error: {e}")

print("\n" + "=" * 60)
print("测试完成 | Test completed")
print("=" * 60)
