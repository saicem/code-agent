#!/usr/bin/env python3
"""
工具管理类
"""

from typing import Iterable

from openai.types.chat import (
    ChatCompletionToolUnionParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionToolMessageParam,
)
from code_agent.tools.base_tool import BaseTool


class ToolManager:
    """工具管理类"""

    # 存储所有注册的工具类
    _registered_tools: dict[str, BaseTool] = {}
    _tools_info: dict[str, ChatCompletionToolUnionParam] = {}

    @classmethod
    def register_tool(cls, tool_class: type[BaseTool]) -> type[BaseTool]:
        """注册工具装饰器

        Args:
            tool_class: 工具类

        Returns:
            工具类
        """
        tool = tool_class()
        tool_name = tool.name()
        cls._registered_tools[tool_name] = tool
        cls._build_tool_info(tool_name, tool)
        return tool_class

    @classmethod
    def get_tool(cls, tool_name: str) -> BaseTool | None:
        """获取工具实例

        Args:
            tool_name: 工具名称

        Returns:
            工具类或 None
        """
        return cls._registered_tools.get(tool_name)

    @classmethod
    def tools_for_model(cls) -> Iterable[ChatCompletionToolUnionParam]:
        """获取所有注册的工具实例

        Returns:
            工具实例列表
        """
        return cls._tools_info.values()

    @classmethod
    def _build_tool_info(cls, name: str, tool: BaseTool):
        """构建工具信息

        Returns:
            工具信息列表
        """
        tool_info: ChatCompletionFunctionToolParam = {
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description(),
                "parameters": tool.parameters(),
            },
        }
        cls._tools_info[name] = tool_info

    @classmethod
    def handle_tool_calls(
        cls, tool_calls: list[ChatCompletionMessageToolCallUnion]
    ) -> list[ChatCompletionToolMessageParam]:
        """处理工具调用

        Args:
            tool_calls: 工具调用列表
        """
        result: list[ChatCompletionToolMessageParam] = []
        for tool_call in tool_calls:
            if tool_call.type == "custom":
                continue
            result.append(
                cls.handle_function_tool_call(tool_call)  # ty:ignore[invalid-argument-type]
            )
        return result

    @classmethod
    def handle_function_tool_call(
        cls, tool_call: ChatCompletionMessageFunctionToolCall
    ) -> ChatCompletionToolMessageParam:
        """处理工具调用"""
        tool = cls.get_tool(tool_call.function.name)
        if tool is None:
            return {
                "content": "工具不存在",
                "role": "tool",
                "tool_call_id": tool_call.id,
            }
        return {
            "content": tool.run(tool_call.function.arguments),
            "role": "tool",
            "tool_call_id": tool_call.id,
        }
