#!/usr/bin/env python
"""
简单HTTP服务器包装器 | Simple HTTP Server Wrapper

直接运行MCP服务器并包装为HTTP接口，无需额外依赖。
Wraps MCP server as HTTP interface without additional dependencies.
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Any, Dict
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess
import signal
import time

# 设置环境变量 | Set environment variables
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# 添加项目路径 | Add project path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


class MCPProcess:
    """MCP服务器进程管理 | MCP server process management."""
    
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    def start(self):
        """启动MCP服务器进程 | Start MCP server process."""
        cmd = [
            sys.executable, "-m", "mcp_sequential_thinking.server",
            "--transport", "stdio"
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_dir
        )
    
    def stop(self):
        """停止MCP服务器进程 | Stop MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    def call(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用MCP方法 | Call MCP method.
        
        Args:
            method: 方法名 | Method name
            params: 参数 | Parameters
        
        Returns:
            响应结果 | Response result
        """
        if not self.process or self.process.poll():
            self.start()
        
        # 构建JSON-RPC请求 | Build JSON-RPC request
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # 发送请求 | Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # 读取响应 | Read response
        response_line = self.process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                if "error" in response:
                    return {"error": response["error"]}
                return response.get("result", {})
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response"}
        
        return {"error": "No response"}


class MCPHTTPHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器 | HTTP request handler."""
    
    mcp_process = MCPProcess()
    
    def do_GET(self):
        """处理GET请求 | Handle GET request."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理POST请求 | Handle POST request."""
        try:
            # 读取请求体 | Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # 解析JSON请求 | Parse JSON request
            request = json.loads(post_data.decode('utf-8'))
            
            # 调用MCP方法 | Call MCP method
            result = self.mcp_process.call(
                request.get("method"),
                request.get("params")
            )
            
            # 返回响应 | Return response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def log_message(self, format, *args):
        """禁用默认日志 | Disable default logging."""
        pass


def main():
    """主函数 | Main function."""
    parser = argparse.ArgumentParser(
        description="Sequential Thinking MCP HTTP服务器 | Sequential Thinking MCP HTTP Server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="监听地址 | Host to bind"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="端口号 | Port number"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Sequential Thinking MCP Server - HTTP Mode")
    print(f"{'='*60}")
    print(f"  监听地址 | Host: {args.host}")
    print(f"  监听端口 | Port: {args.port}")
    print(f"  MCP端点  | Endpoint: http://{args.host}:{args.port}")
    print(f"{'='*60}\n")
    
    # 启动MCP进程 | Start MCP process
    MCPHTTPHandler.mcp_process.start()
    
    # 创建HTTP服务器 | Create HTTP server
    server = HTTPServer((args.host, args.port), MCPHTTPHandler)
    
    # 信号处理 | Signal handling
    def signal_handler(signum, frame):
        print("\n正在停止服务器...")
        MCPHTTPHandler.mcp_process.stop()
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print(f"HTTP服务器已启动 | HTTP server started")
        print(f"健康检查 | Health check: http://{args.host}:{args.port}/health")
        print(f"MCP调用 | MCP calls: POST http://{args.host}:{args.port}")
        print("\n按 Ctrl+C 停止服务器 | Press Ctrl+C to stop server")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止 | Server stopped")
    finally:
        MCPHTTPHandler.mcp_process.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
