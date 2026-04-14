#!/usr/bin/env python3
"""
写入工具
用于写入文件内容
"""

import os
from typing import Dict, Any
from code_agent.tools.base_tool import BaseTool


class WriteTool(BaseTool):
    """写入工具"""

    def __init__(self, base_dir: str = "."):
        """初始化写入工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "write_file"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "写入文件内容到指定路径。当你需要创建或修改文件时使用此工具。"

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
                "content": {
                    "type": "string",
                    "description": "要写入的文件内容",
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "是否覆盖现有文件，默认为 True",
                    "default": True,
                },
            },
            "required": ["file_path", "content"],
        }

    def run(self, **kwargs) -> Dict[str, Any]:
        """运行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具运行结果
        """
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        overwrite = kwargs.get("overwrite", True)

        if not file_path or not content:
            return {
                "success": False,
                "error": "缺少必要参数: file_path 和 content",
            }

        # 构建完整路径
        full_path = os.path.join(self.base_dir, file_path)

        # 确保路径在基础目录内
        if not os.path.abspath(full_path).startswith(self.base_dir):
            return {
                "success": False,
                "error": "文件路径超出允许范围",
            }

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 检查文件是否存在
        if os.path.exists(full_path) and not overwrite:
            return {
                "success": False,
                "error": "文件已存在，且 overwrite 为 False",
            }

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "message": f"文件写入成功: {file_path}",
                "file_path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"写入文件失败: {str(e)}",
            }
