#!/usr/bin/env python3
"""
网络搜索工具
使用 DuckDuckGo 搜索
"""

import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager

from ddgs import DDGS


class SearchParams(BaseModel):
    """Search 工具参数模型"""

    query: str = Field(..., description="搜索查询词")
    limit: int = Field(3, description="返回结果数量，默认为 3")


@ToolManager.register_tool
class SearchTool(BaseTool):
    """网络搜索工具"""

    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        return "search_web"

    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        return "搜索网络内容。当你需要获取最新信息或外部知识时使用此工具。"

    def parameters(self) -> dict[str, Any]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        return {
            "query": {
                "type": "string",
                "description": "搜索查询词",
                "required": True,
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量，默认为 3",
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
                validated_params = SearchParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            try:
                # 使用 DuckDuckGo 搜索
                with DDGS() as ddgs:
                    results = []
                    for result in ddgs.text(
                        validated_params.query,
                        max_results=validated_params.limit,
                    ):
                        results.append(
                            {
                                "title": result.get("title"),
                                "link": result.get("href"),
                                "snippet": result.get("body"),
                            }
                        )

                return json.dumps(
                    {
                        "success": True,
                        "results": results,
                        "query": validated_params.query,
                    },
                    ensure_ascii=False,
                )
            except Exception as e:
                # 如果搜索失败，返回错误信息
                return json.dumps(
                    {
                        "success": False,
                        "message": f"搜索失败: {str(e)}",
                        "query": validated_params.query,
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
                {"success": False, "message": f"搜索失败: {str(e)}"},
                ensure_ascii=False,
            )
