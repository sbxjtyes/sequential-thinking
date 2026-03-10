@echo off
REM 使用虚拟环境启动HTTP服务器
REM Start HTTP server using virtual environment

echo ============================================================
echo Sequential Thinking MCP Server - HTTP Mode
echo ============================================================
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查fastmcp是否安装
python -c "import fastmcp" 2>nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -e .
)

REM 启动服务器
echo 启动服务器 | Starting server...
echo 监听地址 | Host: 0.0.0.0
echo 监听端口 | Port: 8000
echo MCP端点  | Endpoint: http://0.0.0.0:8000/mcp
echo ============================================================
echo.

fastmcp run mcp_sequential_thinking/server.py --transport sse --host 0.0.0.0 --port 8000

pause
