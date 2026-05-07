#!/usr/bin/env python3
"""
写入工具
用于写入文件内容
"""

import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import build_full_path, build_tool_response


class WriteParams(BaseModel):
    """Write 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")
    content: str = Field(..., description="要写入的文件内容")
    overwrite: bool = Field(True, description="是否覆盖现有文件，默认为 True")


@tool(
    name="create_or_overwrite_file",
    description="将内容写入指定路径的文件（默认覆盖现有文件）。适用于创建新文件或完全重写现有文件的场景，区别于局部修改。",
    param_type=WriteParams,
    tags=["code"],
)
def write_file(params: WriteParams) -> str:
    """写入文件

    Args:
        params: 参数对象

    Returns:
        JSON 格式的结果字符串
    """
    full_path = build_full_path(params.file_path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    if os.path.exists(full_path) and not params.overwrite:
        return build_tool_response(
            False,
            "文件已存在，且 overwrite 为 False",
            data={"file_path": params.file_path},
        )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(params.content)

    return build_tool_response(
        True,
        f"文件写入成功: {params.file_path}",
        data={"file_path": params.file_path},
    )
