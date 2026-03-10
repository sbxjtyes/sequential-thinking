#!/usr/bin/env python
"""
启动HTTP服务器（禁用Host检查）
Start HTTP server with Host check disabled
"""

import os
import sys

# 禁用fastmcp的Host header检查
os.environ['FASTMCP_DISABLE_HOST_CHECK'] = '1'

# 导入并运行server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_sequential_thinking.server import main

if __name__ == "__main__":
    # 设置命令行参数
    sys.argv = [
        sys.argv[0],
        '--transport', 'http',
        '--host', '0.0.0.0',
        '--port', '8000'
    ]
    
    print("=" * 60)
    print("Sequential Thinking MCP Server - HTTP Mode")
    print("Host检查已禁用 | Host check disabled")
    print("=" * 60)
    print()
    
    main()
