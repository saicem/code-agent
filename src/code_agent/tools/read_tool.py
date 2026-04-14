#!/usr/bin/env python3
"""
读取工具
用于读取文件内容
"""

import os
from typing import Dict, Any
from code_agent.tools.base_tool import BaseTool


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

    def parameters(self) -> Dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径，相对于项目根目录",
                },
            },
            "required": ["file_path"],
        }

    def run(self, **kwargs) -> Dict[str, Any]:
        """运行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具运行结果
        """
        file_path = kwargs.get("file_path")

        if not file_path:
            return {
                "success": False,
                "error": "缺少必要参数: file_path",
            }

        # 构建完整路径
        full_path = os.path.join(self.base_dir, file_path)

        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(self.base_dir):
            return {
                "success": False,
                "error": "文件路径超出允许范围",
            }

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}",
            }

        # 检查是否是文件
        if not os.path.isfile(full_path):
            return {
                "success": False,
                "error": f"路径不是文件: {file_path}",
            }

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "success": True,
                "content": content,
                "file_path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"读取文件失败: {str(e)}",
            }
