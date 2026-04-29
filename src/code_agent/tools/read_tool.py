#!/usr/bin/env python3
"""
读取工具
用于读取文件内容
"""

import os
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class ReadParams(BaseModel):
    """Read 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")


@ToolManager.register_tool
class ReadTool(BaseTool):
    """读取工具"""

    def __init__(self, base_dir: str = "."):
        """初始化读取工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "read_file"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "读取指定文件的内容。当你需要查看文件内容时使用此工具。"

    def parameters(self) -> dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "file_path": {
                "type": "string",
                "description": "文件路径，相对于项目根目录",
                "required": True,
            },
        }

    def run(self, params: str) -> str:
        """运行工具

        Args:
            params: JSON 格式的参数字符串

        Returns:
            JSON 格式的结果字符串
        """
        try:
            # 使用 Pydantic 验证参数
            try:
                validated_params = ReadParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            # 构建完整路径
            full_path = os.path.join(self.base_dir, validated_params.file_path)
            full_path = os.path.abspath(full_path)

            # 确保路径在基础目录内
            if not full_path.startswith(self.base_dir):
                return json.dumps(
                    {"success": False, "message": "文件路径超出允许范围"},
                    ensure_ascii=False,
                )

            # 检查文件是否存在
            if not os.path.exists(full_path):
                return json.dumps(
                    {"success": False, "message": f"文件不存在: {validated_params.file_path}"},
                    ensure_ascii=False,
                )

            # 检查是否是文件
            if not os.path.isfile(full_path):
                return json.dumps(
                    {"success": False, "message": f"路径不是文件: {validated_params.file_path}"},
                    ensure_ascii=False,
                )

            # 读取文件
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            return json.dumps(
                {"success": True, "content": content, "file_path": validated_params.file_path},
                ensure_ascii=False,
            )

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"读取文件失败: {str(e)}"},
                ensure_ascii=False,
            )
