#!/usr/bin/env python3
"""
按文件名模式搜索文件工具
"""

import asyncio
import glob
import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import build_tool_response


class GlobParams(BaseModel):
    """Glob 工具参数模型"""

    pattern: str = Field(..., description="文件名模式，支持通配符")


def _do_search(pattern: str) -> list[str]:
    """执行文件搜索"""
    pattern = pattern.strip()
    files = glob.glob(pattern, recursive=True)
    return sorted([os.path.relpath(f, os.path.abspath(os.getcwd())) for f in files])


@tool(
    name="find_files_by_pattern",
    description="按文件名模式查找文件（支持通配符 * 和 ?）。适用于根据文件名或扩展名搜索本地文件。",
    param_type=GlobParams,
    tags=["code"],
)
async def search_files(params: GlobParams) -> str:
    """搜索文件

    Args:
        params: 参数对象

    Returns:
        JSON 格式的结果字符串
    """
    files = await asyncio.to_thread(_do_search, params.pattern)

    return build_tool_response(
        True,
        "搜索完成",
        data={"files": files},
    )
