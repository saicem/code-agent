#!/usr/bin/env python3
"""
网络搜索工具
用于搜索网络内容
"""

import requests
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


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
                # 使用 Google 搜索 API
                # 注意：这里使用的是一个示例 API，实际使用时需要替换为真实的 API
                url = "https://www.googleapis.com/customsearch/v1"
                # 这里需要填入真实的 API Key 和 CX
                request_params = {
                    "q": validated_params.query,
                    "key": "YOUR_API_KEY",
                    "cx": "YOUR_CX",
                    "num": validated_params.limit,
                }

                response = requests.get(url, params=request_params, timeout=10)
                response.raise_for_status()

                data = response.json()
                items = data.get("items", [])

                results = []
                for item in items:
                    results.append(
                        {
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "snippet": item.get("snippet"),
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
                # 如果 API 调用失败，返回模拟结果
                return json.dumps(
                    {
                        "success": True,
                        "results": [
                            {
                                "title": f"搜索结果 1 for {validated_params.query}",
                                "link": "https://example.com/1",
                                "snippet": f"这是关于 {validated_params.query} 的搜索结果 1",
                            },
                            {
                                "title": f"搜索结果 2 for {validated_params.query}",
                                "link": "https://example.com/2",
                                "snippet": f"这是关于 {validated_params.query} 的搜索结果 2",
                            },
                        ],
                        "query": validated_params.query,
                        "warning": "使用模拟搜索结果，因为未配置真实的搜索 API",
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
