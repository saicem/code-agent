#!/usr/bin/env python3
"""
文件编辑工具
用于精确替换部分文件内容
"""

import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class EditParams(BaseModel):
    """Edit 工具参数模型"""

    file_path: str = Field(..., description="文件路径")
    old_string: str = Field(..., description="要替换的旧字符串")
    new_string: str = Field(..., description="要替换的新字符串")


@tool(
    name="modify_file_content",
    description="精确替换文件中的指定文本内容。需要提供旧字符串和新字符串，适用于对已有文件进行局部修改的场景，区别于覆盖式写入。",
    param_type=EditParams,
    tags=["code"],
)
def edit_file(params: str) -> str:
    """编辑文件

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    validated_params = validate_params(params, EditParams)
    full_path = build_full_path(validated_params.file_path)

    if not os.path.exists(full_path):
        return build_tool_response(
            False,
            f"文件不存在: {validated_params.file_path}",
        )

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if validated_params.old_string not in content:
        return build_tool_response(
            False,
            "文件中未找到要替换的内容",
        )

    new_content = content.replace(
        validated_params.old_string,
        validated_params.new_string,
    )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return build_tool_response(True, "文件编辑成功")
