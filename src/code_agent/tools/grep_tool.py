#!/usr/bin/env python3
"""
按内容搜索文件工具
"""

import os
import re
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class GrepParams(BaseModel):
    """Grep 工具参数模型"""

    pattern: str = Field(..., description="搜索模式，支持正则表达式")
    path: str | None = Field(None, description="搜索路径，默认为基础目录")
    file_pattern: str = Field("*", description="文件匹配模式，默认为所有文件")


@ToolManager.register_tool
class GrepTool(BaseTool):
    """内容搜索工具"""

    def __init__(self, base_dir: str = "."):
        """初始化内容搜索工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "search_content"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "按内容搜索文件"

    def parameters(self) -> dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "pattern": {
                "type": "string",
                "description": "搜索模式，支持正则表达式",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "搜索路径，默认为基础目录",
                "required": False,
            },
            "file_pattern": {
                "type": "string",
                "description": "文件匹配模式，默认为所有文件",
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
                validated_params = GrepParams.model_validate_json(params)
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

            # 编译正则表达式
            regex = re.compile(validated_params.pattern)

            # 执行搜索
            results = []
            for root, dirs, files in os.walk(full_path):
                # 过滤目录
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    # 检查文件是否匹配模式
                    if not self._match_file_pattern(file, validated_params.file_pattern):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            for line_num, line in enumerate(lines, 1):
                                if regex.search(line):
                                    results.append(
                                        {
                                            "file": os.path.relpath(
                                                file_path, self.base_dir
                                            ),
                                            "line": line_num,
                                            "content": line.strip(),
                                        }
                                    )
                    except Exception:
                        # 跳过无法读取的文件
                        pass

            return json.dumps({"success": True, "results": results}, ensure_ascii=False)

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"搜索内容失败: {str(e)}"},
                ensure_ascii=False,
            )

    def _match_file_pattern(self, file: str, pattern: str) -> bool:
        """检查文件是否匹配模式

        Args:
            file: 文件名
            pattern: 文件匹配模式

        Returns:
            是否匹配
        """
        # 简单的通配符匹配
        if "*" in pattern:
            # 转换为正则表达式
            regex_pattern = pattern.replace("*", ".*")
            return bool(re.match(regex_pattern, file))
        return file == pattern
