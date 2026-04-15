#!/usr/bin/env python3
"""
文件编辑工具
用于精确替换部分文件内容
"""

import os
from typing import Any
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager
from code_agent.assert_tool import AssertTool


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

    def run(self, **kwargs) -> dict[str, Any]:
        """运行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具运行结果
        """
        try:
            # 获取参数
            file_path = AssertTool.assert_type(kwargs.get("file_path"), str)
            old_string = AssertTool.assert_type(kwargs.get("old_string"), str)
            new_string = AssertTool.assert_type(kwargs.get("new_string"), str)

            # 构建完整路径
            full_path = os.path.join(self.base_dir, file_path)
            full_path = os.path.abspath(full_path)

            # 检查路径是否在基础目录内
            if not full_path.startswith(self.base_dir):
                return {
                    "success": False,
                    "message": f"文件路径超出基础目录范围: {file_path}",
                }

            # 检查文件是否存在
            if not os.path.exists(full_path):
                return {"success": False, "message": f"文件不存在: {file_path}"}

            # 读取文件内容
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查旧字符串是否存在
            if old_string not in content:
                return {
                    "success": False,
                    "message": f"文件中未找到要替换的内容: {old_string}",
                }

            # 替换内容
            new_content = content.replace(old_string, new_string)

            # 写入文件
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {"success": True, "message": f"文件编辑成功: {file_path}"}

        except Exception as e:
            return {"success": False, "message": f"编辑文件失败: {str(e)}"}
