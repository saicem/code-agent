#!/usr/bin/env python3
"""
输出工具模块
统一处理各类输出提示，保持界面风格一致
支持颜色输出和日志记录
"""

import logging
import sys

# 获取日志记录器
_logger = logging.getLogger(__name__)


class Color:
    """终端颜色常量"""

    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def get_user_input(prompt: str = "用户输入: ") -> str:
    """获取用户输入

    Args:
        prompt: 输入提示文本

    Returns:
        用户输入的内容
    """
    return input(f"{Color.CYAN}{prompt}{Color.RESET}")


def print_model_output(content: str, prefix: str = "助手") -> None:
    """打印模型输出（蓝色）

    Args:
        content: 模型输出内容
        prefix: 输出前缀
    """
    _logger.info(f"模型输出: {content[:100]}..." if len(content) > 100 else f"模型输出: {content}")
    print(f"{Color.BLUE}{prefix}:{Color.RESET} {content}")


def print_tool_output(content: str, tool_name: str | None = None) -> None:
    """打印工具输出（绿色）

    Args:
        content: 工具输出内容
        tool_name: 工具名称（可选）
    """
    if tool_name:
        _logger.info(
            f"工具 [{tool_name}] 输出: {content[:100]}..."
            if len(content) > 100
            else f"工具 [{tool_name}] 输出: {content}"
        )
        print(f"{Color.GREEN}工具 [{tool_name}]:{Color.RESET} {content}")
    else:
        _logger.info(
            f"工具输出: {content[:100]}..." if len(content) > 100 else f"工具输出: {content}"
        )
        print(f"{Color.GREEN}工具输出:{Color.RESET} {content}")


def print_system_output(content: str, level: str = "info") -> None:
    """打印系统输出（不同级别不同颜色）

    Args:
        content: 系统输出内容
        level: 输出级别（info/warning/error/debug）
    """
    level_config = {
        "info": (Color.BLUE, "[INFO]", sys.stdout, _logger.info),
        "warning": (Color.YELLOW, "[WARN]", sys.stdout, _logger.warning),
        "error": (Color.RED, "[ERROR]", sys.stderr, _logger.error),
        "debug": (Color.MAGENTA, "[DEBUG]", sys.stdout, _logger.debug),
    }

    color, prefix, output_stream, log_func = level_config.get(
        level, (Color.BLUE, "[INFO]", sys.stdout, _logger.info)
    )

    # 记录日志
    log_func(content)

    # 输出到终端
    print(f"{color}{prefix}{Color.RESET} {content}", file=output_stream)


def print_user_message(content: str) -> None:
    """打印用户消息（青色）"""
    _logger.info(f"用户消息: {content}")
    print(f"{Color.CYAN}用户:{Color.RESET} {content}")
