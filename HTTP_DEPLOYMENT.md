# HTTP远程调用部署指南 | HTTP Remote Deployment Guide

本文档说明如何将Sequential Thinking MCP服务器部署到Windows云服务器，并通过HTTP方式从本地电脑远程调用。

This document explains how to deploy the Sequential Thinking MCP server to a Windows cloud server and call it remotely via HTTP from your local computer.

---

## 目录 | Table of Contents

1. [服务器端部署](#服务器端部署--server-deployment)
2. [客户端调用](#客户端调用--client-usage)
3. [网络配置](#网络配置--network-configuration)
4. [常见问题](#常见问题--faq)

---

## 服务器端部署 | Server Deployment

### 1. 环境准备 | Prerequisites

在云服务器上确保已安装：
- Python 3.10+
- uv包管理器（推荐）

```powershell
# 检查Python版本
python --version

# 安装uv（如未安装）
pip install uv
```

### 2. 部署项目 | Deploy Project

将整个项目文件夹复制到云服务器，例如：`C:\mcp\mcp-sequential-thinking`

### 3. 启动HTTP服务 | Start HTTP Server

**推荐方式：直接运行模块**

```powershell
cd C:\mcp\mcp-sequential-thinking
.\.venv\Scripts\activate

# 默认：监听 0.0.0.0:8000，公网可访问
python -m mcp_sequential_thinking.server --transport http --host 0.0.0.0 --port 8000

# 自定义端口
python -m mcp_sequential_thinking.server --transport http --host 0.0.0.0 --port 9000

# 仅本地访问
python -m mcp_sequential_thinking.server --transport http --host 127.0.0.1 --port 8000
```

**备选：使用 uv 运行**

```powershell
cd C:\mcp\mcp-sequential-thinking
uv run mcp-sequential-thinking --transport http --host 0.0.0.0 --port 8000
```

### 4. 验证服务启动 | Verify Server

服务启动后会显示：

```
============================================================
Sequential Thinking MCP Server - HTTP Mode
============================================================
  监听地址 | Host: 0.0.0.0
  监听端口 | Port: 8000
  MCP端点  | Endpoint: http://0.0.0.0:8000/mcp
============================================================
```

在云服务器本地测试：

```powershell
# 测试MCP端点是否可达
curl http://localhost:8000/mcp
```

---

## 客户端调用 | Client Usage

### 1. 安装客户端依赖 | Install Client Dependencies

在本地电脑上：

```powershell
pip install mcp
```

### 2. 客户端调用示例 | Client Example

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamablehttp import streamablehttp_client

async def call_mcp():
    # 连接服务器
    server_url = "http://YOUR_CLOUD_SERVER_IP:8000/mcp"
    client = streamablehttp_client(server_url)
    read, write, _ = await client.__aenter__()
    
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    
    # 调用工具
    result = await session.call_tool("process_thought", {
        "thought": "这是一个测试思考",
        "thought_number": 1,
        "total_thoughts": 1,
        "next_thought_needed": False
    })
    
    print(result)
    
    # 清理
    await session.__aexit__(None, None, None)
    await client.__aexit__(None, None, None)

asyncio.run(call_mcp())
```

---

## 网络配置 | Network Configuration

### Windows防火墙配置 | Windows Firewall

在云服务器上开放端口：

```powershell
# 添加防火墙入站规则（以管理员身份运行）
netsh advfirewall firewall add rule name="MCP Server HTTP" dir=in action=allow protocol=tcp localport=8000

# 验证规则
netsh advfirewall firewall show rule name="MCP Server HTTP"
```

### 云服务商安全组 | Cloud Security Group

根据你的云服务商，在安全组中添加入站规则：
- 协议：TCP
- 端口：8000（或你自定义的端口）
- 来源：0.0.0.0/0（允许所有IP）或指定IP段

**常见云服务商配置入口：**
- 阿里云：ECS实例 > 安全组 > 配置规则
- 腾讯云：CVM实例 > 安全组 > 入站规则
- AWS：EC2 > Security Groups > Inbound Rules
- Azure：虚拟机 > 网络 > 入站端口规则

### 端口占用检查 | Port Conflict Check

```powershell
# 检查端口是否被占用
netstat -ano | findstr :8000

# 如被占用，可更换端口或终止占用进程
```

---

## 常见问题 | FAQ

### Q1: 连接超时

**可能原因：**
1. 服务器未启动
2. 防火墙未开放端口
3. 云服务商安全组未配置
4. IP地址错误

**解决方法：**
```powershell
# 在服务器上检查服务是否运行
netstat -ano | findstr :8000

# 在本地测试网络连通性
ping YOUR_CLOUD_SERVER_IP
telnet YOUR_CLOUD_SERVER_IP 8000
```

### Q2: HTTP 400/500 错误

**可能原因：**
- MCP协议格式不正确
- 服务器内部错误

**解决方法：**
查看服务器日志，确保使用正确的MCP客户端库。

### Q3: 如何设置开机自启

使用Windows任务计划程序或创建Windows服务：

```powershell
# 创建启动脚本 start_mcp.bat
@echo off
cd C:\mcp\mcp-sequential-thinking
call .venv\Scripts\activate.bat
python -m mcp_sequential_thinking.server --transport http --host 0.0.0.0 --port 8000
```

然后在任务计划程序中添加开机启动任务。

### Q4: 如何使用HTTPS

建议使用反向代理（如Nginx）配置SSL证书：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 可用工具列表 | Available Tools

| 工具名称 | 功能描述 |
|---------|---------|
| `process_thought` | 记录单个思考节点并返回分析结果 |
| `generate_summary` | 生成叙事性摘要（narrativeSummary、keyFindings、conclusions、reasoningPath） |
| `clear_history` | 清除当前会话的所有思考历史 |

---

## 参数说明 | Parameter Reference

### process_thought 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|-------|------|
| thought | string | ✓ | - | 思考内容 |
| thought_number | int | ✓ | - | 当前思考序号 |
| total_thoughts | int | ✓ | - | 计划思考总数 |
| next_thought_needed | bool | ✓ | - | 是否需要后续思考 |
| thought_type | string | | analysis | 发散: divergence/analogy/question；收敛: convergence/synthesis/critique；逻辑: hypothesis/verification/analysis/decomposition；元: metacognition/observation/revision |
| stage | string | | Problem Definition | 思考阶段 |
| lang | string | | zh/en | 分析语言 |
| confidence_level | float | | 0.5 | 置信度(0.0-1.0) |
| tags | array | | [] | 标签列表 |
| branch_label | string | | null | 分支标签 |

---

## 技术支持 | Support

如有问题，请查看：
- 项目README：`README.md`
- 示例文档：`example.md`
- 变更日志：`CHANGELOG.md`
