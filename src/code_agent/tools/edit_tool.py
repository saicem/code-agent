#!/usr/bin/env python3
"""
文件编辑工具
用于精确替换部分文件内容
"""

import os
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class EditParams(BaseModel):
    """Edit 工具参数模型"""

    file_path: str = Field(..., description="文件路径")
    old_string: str = Field(..., description="要替换的旧字符串")
    new_string: str = Field(..., description="要替换的新字符串")


@ToolManager.register_tool
class EditTool(BaseTool):
    """文件编辑工具"""

    def __init__(self, base_dir: str = "."):
        """初始化编辑工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "edit_file"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "精确替换文件中的部分内容"

    def parameters(self) -> dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "file_path": {
                "type": "string",
                "description": "文件路径",
                "required": True,
            },
            "old_string": {
                "type": "string",
                "description": "要替换的旧字符串",
                "required": True,
            },
            "new_string": {
                "type": "string",
                "description": "要替换的新字符串",
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
                validated_params = EditParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            # 构建完整路径
            full_path = os.path.join(self.base_dir, validated_params.file_path)
            full_path = os.path.abspath(full_path)

            # 检查路径是否在基础目录内
            if not full_path.startswith(self.base_dir):
                return json.dumps(
                    {
                        "success": False,
                        "message": f"文件路径超出基础目录范围: {validated_params.file_path}",
                    },
                    ensure_ascii=False,
                )

            # 检查文件是否存在
            if not os.path.exists(full_path):
                return json.dumps(
                    {"success": False, "message": f"文件不存在: {validated_params.file_path}"},
                    ensure_ascii=False,
                )

            # 读取文件内容
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查旧字符串是否存在
            if validated_params.old_string not in content:
                return json.dumps(
                    {
                        "success": False,
                        "message": f"文件中未找到要替换的内容: {validated_params.old_string}",
                    },
                    ensure_ascii=False,
                )

            # 替换内容
            new_content = content.replace(validated_params.old_string, validated_params.new_string)

            # 写入文件
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return json.dumps(
                {"success": True, "message": f"文件编辑成功: {validated_params.file_path}"},
                ensure_ascii=False,
            )

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"编辑文件失败: {str(e)}"},
                ensure_ascii=False,
            )
