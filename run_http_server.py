#!/usr/bin/env python
"""
HTTP服务启动脚本 | HTTP Server Startup Script

用于启动支持HTTP传输的MCP服务器，适用于远程调用场景。
Starts the MCP server with HTTP transport for remote access.

使用方式 | Usage:
    # 默认配置（监听0.0.0.0:8000）
    python run_http_server.py
    
    # 自定义端口
    python run_http_server.py --port 9000
    
    # 自定义主机和端口
    python run_http_server.py --host 192.168.1.100 --port 8080
"""

import os
import sys
import subprocess
import argparse

# 设置环境变量确保正确的编码 | Set environment variables for proper encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'


def main():
    """
    启动HTTP模式的MCP服务器 | Start the MCP server in HTTP mode.
    
    使用fastmcp CLI运行HTTP服务器。
    Uses fastmcp CLI to run HTTP server.
    """
    parser = argparse.ArgumentParser(
        description="启动Sequential Thinking MCP HTTP服务器 | Start Sequential Thinking MCP HTTP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 | Examples:
  python run_http_server.py                          # 默认: 0.0.0.0:8000
  python run_http_server.py --port 9000              # 端口9000
  python run_http_server.py --host 127.0.0.1         # 仅本地访问
  python run_http_server.py --host 0.0.0.0 --port 80 # 公网访问，端口80
        """
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="监听地址，默认0.0.0.0（所有接口）。仅本地访问使用127.0.0.1 | Host to bind"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="端口号，默认8000 | Port number"
    )
    
    args = parser.parse_args()
    
    # 设置工作目录 | Set working directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print(f"\n{'='*60}")
    print(f"Sequential Thinking MCP Server - HTTP Mode")
    print(f"{'='*60}")
    print(f"  监听地址 | Host: {args.host}")
    print(f"  监听端口 | Port: {args.port}")
    print(f"  MCP端点  | Endpoint: http://{args.host}:{args.port}/mcp")
    print(f"{'='*60}\n")
    
    # 指定server.py文件的绝对路径 | Use absolute path to server.py
    server_file = os.path.join(project_dir, "mcp_sequential_thinking", "server.py")
    
    # 使用uv运行 | Run with uv
    cmd = [
        "uv", "run", "fastmcp", "run", server_file,
        "--transport", "sse",
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    print(f"执行命令 | Command: {' '.join(cmd)}")
    print()
    
    # 运行服务器 | Run server
    subprocess.run(cmd)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务器已停止 | Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误 | Error: {e}")
        sys.exit(1)
