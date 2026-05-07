#!/usr/bin/env python3
"""
终端命令执行工具
"""

import asyncio
import os

from pydantic import BaseModel, Field

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import build_full_path, build_tool_response


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
async def run_bash(params: BashParams) -> str:
    """执行终端命令

    Args:
        params: 参数对象

    Returns:
        JSON 格式的结果字符串
    """
    full_cwd = build_full_path(params.cwd or ".")

    if not os.path.exists(full_cwd):
        return build_tool_response(False, f"工作目录不存在: {full_cwd}")

    process = await asyncio.create_subprocess_shell(
        params.command,
        cwd=full_cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=30)

    def decode_output(bytes_data: bytes) -> str:
        encodings = ["utf-8", "gbk", "cp1252", "latin-1"]
        for encoding in encodings:
            try:
                return bytes_data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return bytes_data.decode("utf-8", errors="replace")

    stdout = decode_output(stdout_bytes)
    stderr = decode_output(stderr_bytes)

    return build_tool_response(
        process.returncode == 0,
        "命令执行成功" if process.returncode == 0 else "命令执行失败",
        data={
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    )
