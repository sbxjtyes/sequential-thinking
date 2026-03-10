#!/usr/bin/env python
"""
完整的MCP客户端测试
Full MCP client test
"""

import requests
import json

SERVER_URL = "http://106.54.55.203:8000/mcp"

print("=" * 60)
print("MCP服务器完整测试 | Full MCP Server Test")
print("=" * 60)
print(f"服务器地址: {SERVER_URL}\n")

# 测试1: Initialize
print("1. 测试初始化 | Testing initialize...")
try:
    init_request = {
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
        SERVER_URL,
        json=init_request,
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 初始化成功!")
        print(f"   服务器信息: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"   ✗ 失败: {response.text}")
        
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 测试2: List Tools
print("\n2. 测试工具列表 | Testing tools/list...")
try:
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = requests.post(
        SERVER_URL,
        json=tools_request,
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        tools = result.get('result', {}).get('tools', [])
        print(f"   ✓ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"      - {tool.get('name')}: {tool.get('description', '')[:50]}...")
    else:
        print(f"   ✗ 失败: {response.text}")
        
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 测试3: Process Thought
print("\n3. 测试处理思考 | Testing process_thought...")
try:
    thought_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "process_thought",
            "arguments": {
                "thought": "这是一个测试思考，用于验证MCP服务器是否正常工作。",
                "thought_number": 1,
                "total_thoughts": 1,
                "next_thought_needed": False,
                "stage": "测试阶段",
                "lang": "zh"
            }
        }
    }
    
    response = requests.post(
        SERVER_URL,
        json=thought_request,
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 思考处理成功!")
        print(f"   结果: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)[:300]}...")
    else:
        print(f"   ✗ 失败: {response.text}")
        
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 测试4: Generate Summary
print("\n4. 测试生成摘要 | Testing generate_summary...")
try:
    summary_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "generate_summary",
            "arguments": {}
        }
    }
    
    response = requests.post(
        SERVER_URL,
        json=summary_request,
        headers={
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ 摘要生成成功!")
        print(f"   结果: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"   ✗ 失败: {response.text}")
        
except Exception as e:
    print(f"   ✗ 错误: {e}")

print("\n" + "=" * 60)
print("测试完成 | Test completed")
print("=" * 60)
