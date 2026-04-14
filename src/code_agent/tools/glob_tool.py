#!/usr/bin/env python3
"""
文件搜索工具
用于按文件名模式搜索文件
"""

import os
import glob
from typing import Dict, Any, List
from code_agent.tools.base_tool import BaseTool
from code_agent.assert_tool import AssertTool


class GlobTool(BaseTool):
    """文件搜索工具"""

    def __init__(self, base_dir: str = "."):
        """初始化文件搜索工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "search_files"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "按文件名模式搜索文件"

    def parameters(self) -> Dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "pattern": {
                "type": "string",
                "description": "文件名模式，支持通配符",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "搜索路径，默认为基础目录",
                "required": False,
            },
        }

    def run(self, **kwargs) -> Dict[str, Any]:
        """运行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具运行结果
        """
        try:
            # 获取参数
            pattern = AssertTool.assert_type(kwargs.get("pattern"), str)
            path = kwargs.get("path", self.base_dir)

            # 构建完整路径
            if path:
                full_path = os.path.join(self.base_dir, path)
                full_path = os.path.abspath(full_path)

                # 检查路径是否在基础目录内
                if not full_path.startswith(self.base_dir):
                    return {
                        "success": False,
                        "message": f"搜索路径超出基础目录范围: {path}",
                    }
            else:
                full_path = self.base_dir

            # 检查目录是否存在
            if not os.path.exists(full_path):
                return {"success": False, "message": f"搜索路径不存在: {full_path}"}

            # 执行搜索
            search_pattern = os.path.join(full_path, pattern)
            files: List[str] = glob.glob(search_pattern, recursive=True)

            # 转换为相对路径
            relative_files = [os.path.relpath(f, self.base_dir) for f in files]

            return {"success": True, "files": relative_files}

        except Exception as e:
            return {"success": False, "message": f"搜索文件失败: {str(e)}"}
