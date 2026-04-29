#!/usr/bin/env python3
"""
函数调用提取辅助模块
"""

import re


def extract_function_calls(content: str) -> list[str]:
    """从对话内容中提取函数调用信息

    Args:
        content: 模型响应内容

    Returns:
        函数调用信息列表（JSON格式字符串）
    """
    # 首先尝试匹配正确的标签格式
    pattern = r"<tool_call>([\s\S]*?)</tool_call>"
    matches = re.findall(pattern, content)

    # 如果没有找到，尝试匹配错误的标签格式
    if not matches:
        # 匹配可能的错误标签格式，如 </tool_call></tool_call>
        pattern = r"</?tool_call>([\s\S]*?)</?tool_call>"
        matches = re.findall(pattern, content)

    # 清理匹配结果，移除可能的多余标签
    cleaned_matches = []
    for match in matches:
        # 移除可能的标签残留在内容中
        cleaned_match = re.sub(r"</?tool_call>", "", match).strip()
        if cleaned_match:
            cleaned_matches.append(cleaned_match)

    return cleaned_matches
