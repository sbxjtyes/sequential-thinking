"""MCP server for sequential thinking.

Exposes tools for recording thoughts, generating summaries, managing sessions,
and performing analysis through the Model Context Protocol (MCP).
"""

import json
import os
import sys
from typing import List, Optional

from mcp.server.fastmcp import FastMCP, Context

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


mcp = FastMCP("sequential-thinking")

storage = ThoughtStorage()
logger.info("--- In-memory ThoughtStorage initialized ---")

@mcp.tool()
def process_thought(
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
        thought_type: 认知操作类型（可选）。预定义类型：
               "hypothesis"（假设）、"verification"（验证）、"analysis"（分析）、
               "critique"（批判反思）、"synthesis"（综合）、"decomposition"（分解）、
               "observation"（观察）、"revision"（修订）。也接受自定义类型。默认 "analysis"。
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
            ctx.report_progress(thought_number - 1, total_thoughts)

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
def generate_summary() -> dict:
    """
    生成整个思考过程的全局摘要 | Generates a comprehensive summary of the thinking process.

    提供思考会话的鸟瞰视图，包括思考总数、各阶段分布、时间线以及高频标签统计。
    适用于快速回顾和理解整体思考脉络。

    Provides a bird's-eye view of the session, including total thoughts count, distribution
    across stages, timeline, and frequently used tags.

    Returns:
        包含摘要数据的字典 | Dictionary containing comprehensive summary data.
    """
    try:
        logger.info("Generating thinking process summary")
        all_thoughts = storage.get_all_thoughts()
        return ThoughtAnalyzer.generate_summary(all_thoughts)
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def clear_history() -> dict:
    """
    清除当前会话的所有思考历史 | Deletes all thoughts from the current session.

    ⚠️ 警告：这是一个破坏性且不可逆的操作，将永久删除所有已记录的思考。
    执行前请确保已导出重要数据。

    ⚠️ Warning: This is a destructive and irreversible operation. Make sure to
    export important data before executing.

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

@mcp.tool()
def export_session(file_path: str) -> dict:
    """
    将整个思考会话导出为本地 JSON 文件 | Exports the entire thinking session to a local JSON file.

    用于保存、归档和分享思考过程。导出的文件包含完整的思考数据、元数据和时间戳，
    可通过 import_session 工具重新导入。

    Args:
        file_path: 会话文件保存的绝对路径 | Absolute path for saving the session file.

    Returns:
        包含操作状态信息的字典 | Dictionary with operation status message.
    """
    try:
        logger.info(f"Exporting session to {file_path}")
        storage.export_session(file_path)
        return {"status": "success", "message": f"Session exported to {file_path}"}
    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def import_session(file_path: str) -> dict:
    """
    从本地 JSON 文件导入思考会话，覆盖当前会话 | Imports a thinking session from a local JSON file.

    从之前导出的 JSON 文件恢复思考会话。此操作会覆盖当前所有思考记录，
    建议在导入前先导出当前会话以备份。

    Args:
        file_path: 要导入的会话文件的绝对路径 | Absolute path to the session file.

    Returns:
        包含操作状态信息的字典 | Dictionary with operation status message.
    """
    try:
        logger.info(f"Importing session from {file_path}")
        storage.import_session(file_path)
        return {"status": "success", "message": f"Session imported from {file_path}"}
    except Exception as e:
        logger.error(f"Error importing session: {str(e)}")
        return {"error": str(e), "status": "failed"}


def main():
    """Entry point for the MCP server."""
    logger.info("Starting Sequential Thinking MCP server")

    # Ensure UTF-8 encoding for stdin/stdout
    if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    if hasattr(sys.stdin, 'buffer') and sys.stdin.encoding != 'utf-8':
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', line_buffering=True)

    # Flush stdout to ensure no buffered content remains
    sys.stdout.flush()

    # Run the MCP server
    mcp.run()


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
