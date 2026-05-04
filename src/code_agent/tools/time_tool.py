#!/usr/bin/env python3
"""
时间工具
用于获取当前时间
"""

from datetime import datetime

from pydantic import BaseModel

from code_agent.core.exceptions import ToolException
from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_tool_response,
    validate_params,
)


class TimeParams(BaseModel):
    """Time 工具参数模型"""

    pass


@tool(
    name="get_current_time",
    description="获取当前时间。当你需要知道当前时间或处理与时间相关的问题时调用此工具。",
    param_type=TimeParams,
)
async def get_current_time(params: str) -> str:
    """获取当前时间

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    try:
        # 使用统一工具函数校验参数（虽然不需要参数）
        validate_params(params, TimeParams)

        # 获取当前时间（ISO 8601 格式）
        current_time = datetime.now().isoformat()

        return build_tool_response(
            True,
            "获取时间成功",
            data={
                "current_time": current_time,
                "timezone": "UTC+8",
            },
        )

    except ToolException as e:
        return build_tool_response(False, str(e))
    except Exception as e:
        return build_tool_response(False, f"获取时间失败: {e!s}")
