#!/usr/bin/env python3
"""
读取工具
用于读取文件内容
"""

import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import TOOL_TAG_CODE, tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class ReadParams(BaseModel):
    """Read 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")


@tool(
    name="read_file_content",
    description="读取指定本地文件的全部内容。适用于查看文件内容、获取代码或文档内容的场景。",
    param_type=ReadParams,
    tags=[TOOL_TAG_CODE],
)
def read_file(params: str) -> str:
    """读取文件

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    validated_params = validate_params(params, ReadParams)
    full_path = build_full_path(validated_params.file_path)

    if not os.path.exists(full_path):
        return build_tool_response(
            False,
            f"文件不存在: {validated_params.file_path}",
        )

    if not os.path.isfile(full_path):
        return build_tool_response(
            False,
            f"路径不是文件: {validated_params.file_path}",
        )

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return build_tool_response(
        True,
        "读取成功",
        data={
            "content": content,
            "file_path": validated_params.file_path,
        },
    )
