#!/usr/bin/env python3
"""
终端命令执行工具
"""

import os
import subprocess
import json
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class BashParams(BaseModel):
    """Bash 工具参数模型"""

    command: str = Field(..., description="要执行的终端命令")
    cwd: str | None = Field(None, description="命令执行的工作目录，默认为基础目录")


@ToolManager.register_tool(
    name="run_bash",
    description="执行终端命令，例如删除文件、移动文件、查看目录结构等",
    param_type=BashParams,
)
class BashTool(BaseTool):
    """终端命令工具"""

    def __init__(self, base_dir: str = "."):
        """初始化终端命令工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

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
                validated_params = BashParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            # 构建完整路径
            if validated_params.cwd:
                full_cwd = os.path.join(self.base_dir, validated_params.cwd)
                full_cwd = os.path.abspath(full_cwd)

                # 检查路径是否在基础目录内
                if not full_cwd.startswith(self.base_dir):
                    return json.dumps(
                        {
                            "success": False,
                            "message": f"工作目录超出基础目录范围: {validated_params.cwd}",
                        },
                        ensure_ascii=False,
                    )
            else:
                full_cwd = self.base_dir

            # 检查目录是否存在
            if not os.path.exists(full_cwd):
                return json.dumps(
                    {"success": False, "message": f"工作目录不存在: {full_cwd}"},
                    ensure_ascii=False,
                )

            # 执行命令
            result = subprocess.run(
                validated_params.command,
                shell=True,
                cwd=full_cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return json.dumps(
                {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
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
                {"success": False, "message": f"执行命令失败: {str(e)}"},
                ensure_ascii=False,
            )
