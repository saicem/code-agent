#!/usr/bin/env python3
"""
时间工具
用于获取当前时间
"""

import json
from datetime import datetime
from pydantic import BaseModel, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class TimeParams(BaseModel):
    """Time 工具参数模型"""

    pass


@ToolManager.register_tool(
    name="get_current_time",
    description="获取当前时间。当你需要知道当前时间或处理与时间相关的问题时调用此工具。",
    param_type=TimeParams,
)
class TimeTool(BaseTool):
    """获取当前时间工具"""

    def run(self, params: str) -> str:
        """运行工具

        Args:
            params: JSON 格式的参数字符串

        Returns:
            JSON 格式的结果字符串
        """
        try:
            # 使用 Pydantic 验证参数（虽然不需要参数）
            try:
                TimeParams.model_validate_json(params)
            except ValidationError:
                # 如果参数无效，尝试解析为空对象
                pass

            # 获取当前时间（ISO 8601 格式）
            current_time = datetime.now().isoformat()

            return json.dumps(
                {
                    "success": True,
                    "message": "获取时间成功",
                    "current_time": current_time,
                    "timezone": "UTC+8",
                },
                ensure_ascii=False,
            )

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"获取时间失败: {str(e)}"},
                ensure_ascii=False,
            )
