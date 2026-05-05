#!/usr/bin/env python3
"""
网络搜索工具
使用 DuckDuckGo 搜索
"""

from ddgs import DDGS
from pydantic import BaseModel, Field

from code_agent.core.exceptions import ToolException
from code_agent.tools._manager import tool
from code_agent.utils.tool_util import (
    build_tool_response,
    validate_params,
)


class SearchParams(BaseModel):
    """Search 工具参数模型"""

    query: str = Field(..., description="搜索查询词")
    limit: int = Field(3, description="返回结果数量，默认为 3")


@tool(
    name="web_search",
    description="通过搜索引擎搜索互联网内容，获取最新资讯、技术文档、外部知识等。适用于需要查找外部信息的场景，区别于本地文件搜索。",
    param_type=SearchParams,
)
async def search_web(params: str) -> str:
    """搜索网络内容

    Args:
        params: JSON 格式的参数字符串

    Returns:
        JSON 格式的结果字符串
    """
    try:
        # 使用统一工具函数校验参数
        validated_params = validate_params(params, SearchParams)

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

            return build_tool_response(
                True,
                "搜索完成",
                data={
                    "results": results,
                    "query": validated_params.query,
                },
            )
        except Exception as e:
            # 如果搜索失败，返回错误信息
            return build_tool_response(
                False,
                f"搜索失败: {e!s}",
                data={"query": validated_params.query},
            )

    except ToolException as e:
        return build_tool_response(False, str(e))
    except Exception as e:
        return build_tool_response(False, f"搜索失败: {e!s}")
