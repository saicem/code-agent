#!/usr/bin/env python3
"""
按文件名模式搜索文件工具
"""
import asyncio
import glob
import os

from pydantic import BaseModel, Field

from code_agent.core.exceptions import ToolException
from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class GlobParams(BaseModel):
    """Glob 工具参数模型"""

    pattern: str = Field(..., description="文件名模式，支持通配符")
    path: str | None = Field(None, description="搜索路径，默认为基础目录")


def _do_search(full_path: str, pattern: str) -> list[str]:
    """执行文件搜索"""
    pattern = pattern.strip()

    # 移除可能的工具名前缀
    tool_prefixes = ["glob_tool", "search_files", "search"]
    for prefix in tool_prefixes:
        if pattern.lower().startswith(prefix.lower()):
            pattern = pattern[len(prefix) :]
            break

    # 处理多个模式
    if "|" in pattern:
        patterns = [p.strip() for p in pattern.split("|") if p.strip()]
    else:
        patterns = [pattern]

    # 执行搜索
    all_files: set[str] = set()
    base_dir = os.path.abspath(os.getcwd())
    for pat in patterns:
        if pat and not os.path.dirname(pat) and not pat.startswith("**"):
            pat = os.path.join("**", pat)

        search_pattern = os.path.join(full_path, pat)
        try:
            files = glob.glob(search_pattern, recursive=True)
            all_files.update(files)
        except Exception:
            continue

    return sorted([os.path.relpath(f, base_dir) for f in all_files])


@tool(
    name="search_files",
    description="按文件名模式搜索文件，支持通配符 * 和 ?，支持使用 | 分隔多个模式",
    param_type=GlobParams,
)
async def search_files(params: str) -> str:
    """搜索文件

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    try:
        # 使用统一工具函数校验参数
        validated_params = validate_params(params, GlobParams)
        full_path = build_full_path(validated_params.path or ".")

        # 检查目录是否存在
        if not os.path.exists(full_path):
            return build_tool_response(
                False,
                f"搜索路径不存在: {full_path}",
            )

        # 异步执行搜索
        files = await asyncio.to_thread(_do_search, full_path, validated_params.pattern)

        return build_tool_response(
            True,
            "搜索完成",
            data={"files": files},
        )

    except ToolException as e:
        return build_tool_response(False, str(e))
    except Exception as e:
        return build_tool_response(False, f"搜索文件失败: {e!s}")
