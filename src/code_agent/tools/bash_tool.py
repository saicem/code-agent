#!/usr/bin/env python3
"""
终端命令工具
用于执行终端命令
"""

import os
import subprocess
from typing import Dict, Any
from code_agent.tools.base_tool import BaseTool
from code_agent.assert_tool import AssertTool


class BashTool(BaseTool):
    """终端命令工具"""

    def __init__(self, base_dir: str = "."):
        """初始化终端命令工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "run_bash"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "执行终端命令，例如删除文件、移动文件、查看目录结构等"

    def parameters(self) -> Dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "command": {
                "type": "string",
                "description": "要执行的终端命令",
                "required": True,
            },
            "cwd": {
                "type": "string",
                "description": "命令执行的工作目录，默认为基础目录",
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
            command = AssertTool.assert_type(kwargs.get("command"), str)
            cwd = kwargs.get("cwd", self.base_dir)

            # 构建完整路径
            if cwd:
                full_cwd = os.path.join(self.base_dir, cwd)
                full_cwd = os.path.abspath(full_cwd)

                # 检查路径是否在基础目录内
                if not full_cwd.startswith(self.base_dir):
                    return {
                        "success": False,
                        "message": f"工作目录超出基础目录范围: {cwd}",
                    }
            else:
                full_cwd = self.base_dir

            # 检查目录是否存在
            if not os.path.exists(full_cwd):
                return {"success": False, "message": f"工作目录不存在: {full_cwd}"}

            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=full_cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except Exception as e:
            return {"success": False, "message": f"执行命令失败: {str(e)}"}
