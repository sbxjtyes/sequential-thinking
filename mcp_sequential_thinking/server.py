"""MCP server for sequential thinking.

Exposes tools for recording thoughts, generating summaries, managing sessions,
and performing analysis through the Model Context Protocol (MCP).
"""

import json
import os
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.transport_security import TransportSecuritySettings

# Use absolute imports when running as a script
try:
    # When installed as a package
    from .models import ThoughtData, ThoughtStage
    from .storage import ThoughtStorage
    from .analysis import ThoughtAnalyzer
    from .logging_conf import configure_logging
    from .config import config
except ImportError:
    # When run directly
    from mcp_sequential_thinking.models import ThoughtData, ThoughtStage
    from mcp_sequential_thinking.storage import ThoughtStorage
    from mcp_sequential_thinking.analysis import ThoughtAnalyzer
    from mcp_sequential_thinking.logging_conf import configure_logging
    from mcp_sequential_thinking.config import config

logger = configure_logging("sequential-thinking.server")


# 公网部署时需关闭 DNS rebinding 保护，否则 Host 为公网 IP（如 106.54.55.203:8000）会被拒绝
# When deploying publicly, disable DNS rebinding protection so clients can connect via public IP
mcp = FastMCP(
    "sequential-thinking",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)

storage = ThoughtStorage()
logger.info("--- In-memory ThoughtStorage initialized ---")

@mcp.tool()
async def process_thought(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    thought_type: str = "analysis",
    stage: str = "Problem Definition",
    parent_thought_id: Optional[str] = None,
    revises_thought_id: Optional[str] = None,
    branch_label: Optional[str] = None,
    tags: Optional[List[str]] = None,
    axioms_used: Optional[List[str]] = None,
    assumptions_challenged: Optional[List[str]] = None,
    confidence_level: float = 0.5,
    supporting_evidence: Optional[List[str]] = None,
    counter_arguments: Optional[List[str]] = None,
    lang: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict:
    """
    记录单个思考节点并返回深度分析结果（含自动反思） | Records a thought with analysis and reflection.

    这是构建结构化推理链的核心工具。每个思考都标记了认知操作类型（假设/验证/分析/反思/综合等），
    支持树状分支探索和修订。系统会自动检测推理模式并生成反思提示，引导更严谨的深度思考。

    This is the core tool for building a structured reasoning chain. Each thought is tagged
    with a cognitive operation type (hypothesis/verification/analysis/critique/synthesis etc.),
    supports tree-structured branching and revision. The system automatically detects reasoning
    patterns and generates reflection prompts for more rigorous thinking.

    Args:
        thought: 思考的主要内容 | The main content of the thought.
        thought_number: 当前思考的序号 | Sequence number of this thought.
        total_thoughts: 计划的思考总数 | Total number of thoughts planned.
        next_thought_needed: 是否还需要后续思考 | Whether more thoughts are expected.
        thought_type: 认知操作类型（可选）。发散：divergence（发散）、analogy（类比）、
               question（提问）；收敛：convergence（收敛）、synthesis（综合）、critique（批判）；
               逻辑：hypothesis（假设）、verification（验证）、analysis（分析）、
               decomposition（分解）；元认知：metacognition（元认知）、observation（观察）、
               revision（修订）。默认 "analysis"。
               | Cognitive operation type. Defaults to "analysis".
        stage: 思考所属阶段，接受任意字符串 | The thinking stage. Any string is accepted.
        parent_thought_id: 父思考的 UUID（用于树状分支），null 表示根节点 |
               UUID of parent thought for tree-structured reasoning.
        revises_thought_id: 被修订思考的 UUID（标记修正关系）|
               UUID of the earlier thought being revised.
        branch_label: 分支标签（如 "方案A"、"方案B"）| Branch label for exploration paths.
        tags: 关键词列表（可选）| Optional keywords for categorization.
        axioms_used: 所依据的原则列表（可选）| Optional principles relied upon.
        assumptions_challenged: 被质疑的假设列表（可选）| Optional challenged assumptions.
        confidence_level: 置信度 0.0-1.0，默认 0.5 | Confidence score, defaults to 0.5.
        supporting_evidence: 支持证据列表（可选）| Optional supporting evidence.
        counter_arguments: 反驳论点列表（可选）| Optional counter-arguments.
        lang: 分析语言 'en'/'zh' | Language for analysis, defaults to config.
        ctx: MCP 上下文对象 | MCP context for progress reporting.

    Returns:
        包含分析结果和反思提示的字典 | Dict with analysis results and reflection prompts.
    """
    try:
        # Set language from config if not provided
        final_lang = lang if lang is not None else config.features.semantic_analysis.default_lang

        logger.info(f"Processing thought #{thought_number}/{total_thoughts} [{thought_type}] in stage '{stage}' for language '{final_lang}'")

        if ctx:
            await ctx.report_progress(thought_number - 1, total_thoughts)

        thought_data = ThoughtData(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            thought_type=thought_type,
            stage=stage,
            parent_thought_id=parent_thought_id,
            revises_thought_id=revises_thought_id,
            branch_label=branch_label,
            tags=tags or [],
            axioms_used=axioms_used or [],
            assumptions_challenged=assumptions_challenged or [],
            confidence_level=confidence_level,
            supporting_evidence=supporting_evidence or [],
            counter_arguments=counter_arguments or [],
        )

        storage.add_thought(thought_data)

        all_thoughts = storage.get_all_thoughts()
        analysis = ThoughtAnalyzer.analyze_thought(thought_data, all_thoughts, lang=final_lang)

        logger.info(f"Successfully processed thought #{thought_number}")
        return analysis
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {"error": f"JSON parsing error: {str(e)}", "status": "failed"}
    except Exception as e:
        logger.error(f"Error processing thought: {e}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def generate_summary(lang: Optional[str] = None) -> dict:
    """
    生成整个思考过程的真实摘要 | Generates a real narrative summary of the thinking process.

    产出可读的叙事性总结，包括：各阶段核心要点(narrativeSummary)、关键发现(keyFindings)、
    结论(conclusions)、推理路径(reasoningPath)。便于 LLM 做最终综合。

    Produces readable narrative text: key points per stage, findings, conclusions, reasoning path.

    Args:
        lang: 摘要语言 'zh'/'en'，默认从配置读取 | Summary language.

    Returns:
        包含 narrativeSummary、keyFindings、conclusions、reasoningPath 的字典。
    """
    try:
        logger.info("Generating thinking process summary")
        all_thoughts = storage.get_all_thoughts()
        final_lang = lang or config.features.semantic_analysis.default_lang
        return ThoughtAnalyzer.generate_summary(all_thoughts, lang=final_lang)
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def clear_history() -> dict:
    """
    清除当前会话的所有思考历史 | Deletes all thoughts from the current session.

    ⚠️ 警告：这是一个破坏性且不可逆的操作，将永久删除所有已记录的思考。

    ⚠️ Warning: This is a destructive and irreversible operation.

    Returns:
        包含操作状态信息的字典 | Dictionary with operation status message.
    """
    try:
        logger.info("Clearing thought history")
        storage.clear_history()
        return {"status": "success", "message": "Thought history cleared."}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return {"error": str(e), "status": "failed"}


def main():
    """
    MCP服务入口点 | Entry point for the MCP server.
    
    支持多种传输模式：
    - STDIO（默认）：通过标准输入输出通信，适用于本地进程间通信
    - HTTP：通过HTTP协议通信，适用于远程调用和Web集成
    - SSE：通过Server-Sent Events通信（旧版，建议使用HTTP代替）
    
    Supports multiple transport modes:
    - STDIO (default): Communication via stdin/stdout, suitable for local IPC
    - HTTP: Communication via HTTP protocol, suitable for remote calls and web integration
    - SSE: Communication via Server-Sent Events (legacy, prefer HTTP for new projects)
    """
    import argparse
    
    # 解析命令行参数 | Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Sequential Thinking MCP Server - 顺序思考MCP服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 | Examples:
  # STDIO模式（默认）| STDIO mode (default)
  python -m mcp_sequential_thinking.server
  
  # HTTP模式，监听所有接口 | HTTP mode, listen on all interfaces
  python -m mcp_sequential_thinking.server --transport http --host 0.0.0.0 --port 8000
  
  # SSE模式（旧版）| SSE mode (legacy)
  python -m mcp_sequential_thinking.server --transport sse --port 8080
        """
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="传输模式：stdio（默认）、http（推荐用于远程）、sse（旧版）| Transport mode"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP/SSE模式监听地址，默认127.0.0.1（仅本地）。远程部署建议使用0.0.0.0 | Host to bind"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="HTTP/SSE模式端口号，默认8000 | Port number for HTTP/SSE mode"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting Sequential Thinking MCP server with {args.transport} transport")
    
    if args.transport in ["http", "sse"]:
        logger.info(f"Server will be available at http://{args.host}:{args.port}")
        if args.transport == "http":
            logger.info(f"MCP endpoint: http://{args.host}:{args.port}/mcp")

    # Ensure UTF-8 encoding for stdin/stdout (for STDIO mode)
    if args.transport == "stdio":
        if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        if hasattr(sys.stdin, 'buffer') and sys.stdin.encoding != 'utf-8':
            import io
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', line_buffering=True)

    # Flush stdout to ensure no buffered content remains
    sys.stdout.flush()

    # Set host/port for HTTP/SSE transport.
    # FastMCP streamable-http ignores env vars and often binds to 127.0.0.1.
    # Use mcp.settings (if available) to force host/port before run().
    if args.transport in ["http", "sse"]:
        os.environ["FASTMCP_HOST"] = args.host
        os.environ["FASTMCP_PORT"] = str(args.port)
        if args.host not in ["127.0.0.1", "localhost"]:
            os.environ["FASTMCP_DISABLE_HOST_CHECK"] = "1"
        # Explicitly set host/port on FastMCP settings so Uvicorn binds correctly
        if hasattr(mcp, "settings"):
            mcp.settings.host = args.host
            mcp.settings.port = args.port
            logger.info(f"FastMCP settings: host={mcp.settings.host}, port={mcp.settings.port}")

    # Run the MCP server with specified transport
    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="streamable-http")
    elif args.transport == "sse":
        mcp.run(transport="sse")


if __name__ == "__main__":
    # When running the script directly, ensure we're in the right directory
    # (os and sys are already imported at the top of this file)
    # Add the parent directory to sys.path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Print debug information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    logger.info(f"Parent directory added to path: {parent_dir}")

    # Run the server
    main()
