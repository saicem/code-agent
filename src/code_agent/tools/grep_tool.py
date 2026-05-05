#!/usr/bin/env python3
"""
按内容搜索文件工具
"""

import asyncio
import os
import re

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class GrepParams(BaseModel):
    """Grep 工具参数模型"""

    pattern: str = Field(..., description="搜索模式，支持正则表达式")
    path: str | None = Field(None, description="搜索路径，默认为基础目录")
    file_pattern: str = Field("*", description="文件匹配模式，默认为所有文件")


def _match_file_pattern(file: str, pattern: str) -> bool:
    """检查文件是否匹配模式"""
    if "*" in pattern:
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, file))
    return file == pattern


def _do_search(full_path: str, pattern: str, file_pattern: str) -> list[dict]:
    """执行内容搜索"""
    regex = re.compile(pattern)
    results = []
    base_dir = os.path.abspath(os.getcwd())

    for root, dirs, files in os.walk(full_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if not _match_file_pattern(file, file_pattern):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            results.append(
                                {
                                    "file": os.path.relpath(file_path, base_dir),
                                    "line": line_num,
                                    "content": line.strip(),
                                }
                            )
            except Exception:
                pass

    return results


@tool(
    name="search_text_in_files",
    description="在本地文件中搜索包含指定文本内容的文件（正则表达式）。适用于查找包含特定代码、字符串的文件。",
    param_type=GrepParams,
    tags=["code"],
)
async def search_content(params: str) -> str:
    """搜索内容

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    # 使用统一工具函数校验参数
    validated_params = validate_params(params, GrepParams)
    full_path = build_full_path(validated_params.path or ".")

    # 检查目录是否存在
    if not os.path.exists(full_path):
        return build_tool_response(
            False,
            f"搜索路径不存在: {full_path}",
        )

    # 异步执行搜索
    results = await asyncio.to_thread(
        _do_search,
        full_path,
        validated_params.pattern,
        validated_params.file_pattern,
    )

    return build_tool_response(
        True,
        "搜索完成",
        data={"results": results},
    )
