#!/usr/bin/env python3
"""
写入工具
用于写入文件内容
"""

import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import TOOL_TAG_CODE, tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class WriteParams(BaseModel):
    """Write 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")
    content: str = Field(..., description="要写入的文件内容")
    overwrite: bool = Field(True, description="是否覆盖现有文件，默认为 True")


@tool(
    name="create_or_overwrite_file",
    description="将内容写入指定路径的文件（默认覆盖现有文件）。适用于创建新文件或完全重写现有文件的场景，区别于局部修改。",
    param_type=WriteParams,
    tags=[TOOL_TAG_CODE],
)
def write_file(params: str) -> str:
    """写入文件

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    # 使用统一工具函数校验参数
    validated_params = validate_params(params, WriteParams)
    full_path = build_full_path(validated_params.file_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 检查文件是否存在
    if os.path.exists(full_path) and not validated_params.overwrite:
        return build_tool_response(
            False,
            "文件已存在，且 overwrite 为 False",
            data={"file_path": validated_params.file_path},
        )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(validated_params.content)

    return build_tool_response(
        True,
        f"文件写入成功: {validated_params.file_path}",
        data={"file_path": validated_params.file_path},
    )
