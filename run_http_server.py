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
import argparse

# 设置环境变量确保正确的编码 | Set environment variables for proper encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'


def main():
    """
    启动HTTP模式的MCP服务器 | Start the MCP server in HTTP mode.
    
    使用uvicorn运行ASGI应用实现HTTP传输。
    Uses uvicorn to run ASGI application for HTTP transport.
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
    
    # 确保项目目录在路径中 | Ensure project directory is in path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # 导入MCP服务器 | Import MCP server
    from mcp_sequential_thinking.server import mcp
    from mcp_sequential_thinking.logging_conf import configure_logging
    
    logger = configure_logging("sequential-thinking.http_runner")
    
    print(f"\n{'='*60}")
    print(f"Sequential Thinking MCP Server - HTTP Mode")
    print(f"{'='*60}")
    print(f"  监听地址 | Host: {args.host}")
    print(f"  监听端口 | Port: {args.port}")
    print(f"  MCP端点  | Endpoint: http://{args.host}:{args.port}/mcp")
    print(f"{'='*60}\n")
    
    logger.info(f"Starting HTTP server on {args.host}:{args.port}")
    
    # 获取ASGI应用并使用uvicorn运行 | Get ASGI app and run with uvicorn
    import uvicorn
    app = mcp.http_app()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务器已停止 | Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误 | Error: {e}")
        sys.exit(1)
