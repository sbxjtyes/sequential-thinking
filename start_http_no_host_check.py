#!/usr/bin/env python
"""
启动HTTP服务器（禁用Host检查）
Start HTTP server with Host check disabled
"""

import os
import sys

# 设置fastmcp环境变量
os.environ['FASTMCP_HOST'] = '0.0.0.0'
os.environ['FASTMCP_PORT'] = '8000'
os.environ['FASTMCP_DISABLE_HOST_CHECK'] = '1'

# 导入并运行server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Sequential Thinking MCP Server - HTTP Mode")
print("Host: 0.0.0.0")
print("Port: 8000")
print("Host检查已禁用 | Host check disabled")
print("=" * 60)
print()

# 直接使用fastmcp CLI
import subprocess
subprocess.run([
    sys.executable, '-m', 'mcp_sequential_thinking.server',
    '--transport', 'streamable-http'
])
