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
        return "按文件名模式搜索文件，支持通配符 * 和 ?，支持使用 | 分隔多个模式"

    def parameters(self) -> dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "pattern": {
                "type": "string",
                "description": "文件名模式，支持通配符 * 和 ?，多个模式可用 | 分隔",
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

            # 处理模式
            pattern = validated_params.pattern.strip()

            # 移除可能的工具名前缀（如 glob_tool* -> *）
            tool_prefixes = ["glob_tool", "search_files", "search"]
            for prefix in tool_prefixes:
                if pattern.lower().startswith(prefix.lower()):
                    pattern = pattern[len(prefix) :]
                    break

            # 处理多个模式（用 | 分隔）
            if "|" in pattern:
                patterns = [p.strip() for p in pattern.split("|") if p.strip()]
            else:
                patterns = [pattern]

            # 执行搜索
            all_files: set[str] = set()
            for pat in patterns:
                # 如果模式不包含路径分隔符，自动添加 **/ 前缀以搜索所有子目录
                if pat and not os.path.dirname(pat) and not pat.startswith("**"):
                    pat = os.path.join("**", pat)

                search_pattern = os.path.join(full_path, pat)
                try:
                    files = glob.glob(search_pattern, recursive=True)
                    all_files.update(files)
                except Exception:
                    # 忽略无效的模式
                    continue

            # 转换为相对路径并排序
            relative_files = sorted(
                [os.path.relpath(f, self.base_dir) for f in all_files]
            )

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
