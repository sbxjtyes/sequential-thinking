#!/usr/bin/env python
"""
详细的MCP服务器测试
Detailed MCP server test
"""

import requests
import json
import time

SERVER_IP = "106.54.55.203"
PORTS = [8000, 8080, 3000, 5000]  # 测试多个常用端口

print("=" * 60)
print("MCP服务器详细测试 | Detailed MCP Server Test")
print("=" * 60)

for port in PORTS:
    print(f"\n测试端口 {port} | Testing port {port}...")
    print("-" * 40)
    
    # 测试根路径
    try:
        url = f"http://{SERVER_IP}:{port}/"
        response = requests.get(url, timeout=3)
        print(f"  ✓ 根路径可访问 | Root accessible")
        print(f"    状态码: {response.status_code}")
        print(f"    响应: {response.text[:100]}")
    except requests.exceptions.Timeout:
        print(f"  ✗ 超时 | Timeout")
        continue
    except requests.exceptions.ConnectionError:
        print(f"  ✗ 无法连接 | Connection refused")
        continue
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        continue
    
    # 测试/mcp路径
    try:
        url = f"http://{SERVER_IP}:{port}/mcp"
        response = requests.get(url, timeout=3)
        print(f"  /mcp 状态码: {response.status_code}")
    except Exception as e:
        print(f"  /mcp 错误: {e}")
    
    # 测试/sse路径
    try:
        url = f"http://{SERVER_IP}:{port}/sse"
        response = requests.get(url, timeout=3)
        print(f"  /sse 状态码: {response.status_code}")
    except Exception as e:
        pass
    
    # 尝试MCP调用
    try:
        url = f"http://{SERVER_IP}:{port}/mcp"
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        response = requests.post(
            url,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        print(f"  ✓ MCP调用成功 | MCP call successful")
        print(f"    响应: {response.text[:200]}")
        
        # 如果成功，这就是正确的端口
        print(f"\n✓✓✓ 找到工作端口: {port} ✓✓✓")
        print(f"正确的URL: http://{SERVER_IP}:{port}/mcp")
        break
        
    except Exception as e:
        pass

print("\n" + "=" * 60)
print("测试完成 | Test completed")
print("=" * 60)
