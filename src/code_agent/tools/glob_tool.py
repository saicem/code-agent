#!/usr/bin/env python3
"""
按文件名模式搜索文件工具
"""

import os
import glob
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class GlobParams(BaseModel):
    """Glob 工具参数模型"""

    pattern: str = Field(..., description="文件名模式，支持通配符")
    path: str | None = Field(None, description="搜索路径，默认为基础目录")


@ToolManager.register_tool
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

    def parameters(self) -> dict[str, Any]:
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
                validated_params = GlobParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            # 构建完整路径
            if validated_params.path:
                full_path = os.path.join(self.base_dir, validated_params.path)
                full_path = os.path.abspath(full_path)

                # 检查路径是否在基础目录内
                if not full_path.startswith(self.base_dir):
                    return json.dumps(
                        {
                            "success": False,
                            "message": f"搜索路径超出基础目录范围: {validated_params.path}",
                        },
                        ensure_ascii=False,
                    )
            else:
                full_path = self.base_dir

            # 检查目录是否存在
            if not os.path.exists(full_path):
                return json.dumps(
                    {"success": False, "message": f"搜索路径不存在: {full_path}"},
                    ensure_ascii=False,
                )

            # 执行搜索
            search_pattern = os.path.join(full_path, validated_params.pattern)
            files = glob.glob(search_pattern, recursive=True)

            # 转换为相对路径
            relative_files = [os.path.relpath(f, self.base_dir) for f in files]

            return json.dumps(
                {"success": True, "files": relative_files}, ensure_ascii=False
            )

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"搜索文件失败: {str(e)}"},
                ensure_ascii=False,
            )
