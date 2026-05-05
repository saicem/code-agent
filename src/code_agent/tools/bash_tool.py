#!/usr/bin/env python3
"""
终端命令执行工具
"""

import asyncio
import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_full_path,
    build_tool_response,
    validate_params,
)


class BashParams(BaseModel):
    """Bash 工具参数模型"""

    command: str = Field(..., description="要执行的终端命令")
    cwd: str | None = Field(None, description="命令执行的工作目录，默认为基础目录")


@tool(
    name="execute_command",
    description="执行系统终端命令（如删除、移动、复制文件，查看目录结构，运行程序等）。适用于需要操作系统层面操作的场景。",
    param_type=BashParams,
    tags=["code"],
)
async def run_bash(params: str) -> str:
    """执行终端命令

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    # 使用统一工具函数校验参数
    validated_params = validate_params(params, BashParams)
    full_cwd = build_full_path(validated_params.cwd or ".")

    # 检查目录是否存在
    if not os.path.exists(full_cwd):
        return build_tool_response(False, f"工作目录不存在: {full_cwd}")

    process = await asyncio.create_subprocess_shell(
        validated_params.command,
        cwd=full_cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=30)

    # 尝试解码输出
    try:
        stdout = stdout_bytes.decode("utf-8")
        stderr = stderr_bytes.decode("utf-8")
    except UnicodeDecodeError:
        stdout = stdout_bytes.decode()
        stderr = stderr_bytes.decode()

    return build_tool_response(
        process.returncode == 0,
        "命令执行成功" if process.returncode == 0 else "命令执行失败",
        data={
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    )
