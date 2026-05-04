#!/usr/bin/env python3
"""
读取工具
用于读取文件内容
"""
import asyncio
import os

from pydantic import BaseModel, Field

from code_agent.core.exceptions import ToolException
from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class ReadParams(BaseModel):
    """Read 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")


@tool(
    name="read_file",
    description="读取指定文件的内容。当你需要查看文件内容时使用此工具。",
    param_type=ReadParams,
)
async def read_file(params: str) -> str:
    """读取文件

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    try:
        # 使用统一工具函数校验参数
        validated_params = validate_params(params, ReadParams)
        full_path = build_full_path(validated_params.file_path)

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return build_tool_response(
                False,
                f"文件不存在: {validated_params.file_path}",
            )

        # 检查是否是文件
        if not os.path.isfile(full_path):
            return build_tool_response(
                False,
                f"路径不是文件: {validated_params.file_path}",
            )

        # 异步读取文件
        content = await asyncio.to_thread(lambda: open(full_path, "r", encoding="utf-8").read())

        return build_tool_response(
            True,
            "读取成功",
            data={
                "content": content,
                "file_path": validated_params.file_path,
            },
        )

    except ToolException as e:
        return build_tool_response(False, str(e))
    except Exception as e:
        return build_tool_response(False, f"读取文件失败: {e!s}")
