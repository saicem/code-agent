#!/usr/bin/env python3
"""
时间工具
用于获取当前时间
"""

from datetime import datetime

from pydantic import BaseModel

from code_agent.tools._manager import tool
from code_agent.utils.tool_util import build_tool_response


class TimeParams(BaseModel):
    """Time 工具参数模型"""

    pass


@tool(
    name="retrieve_current_time",
    description="获取当前系统时间。适用于需要时间戳、日志记录或时间相关计算的场景。",
    param_type=TimeParams,
    tags=["code", "plan"],
)
async def get_current_time(params: TimeParams) -> str:
    """获取当前时间

    Args:
        params: 参数对象

    Returns:
        JSON 格式的结果字符串
    """
    current_time = datetime.now().isoformat()

    return build_tool_response(
        True,
        "获取时间成功",
        data={
            "current_time": current_time,
            "timezone": "UTC+8",
        },
    )
