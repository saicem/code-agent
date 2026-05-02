#!/usr/bin/env python3
"""
工具管理类
"""
from code_agent.helpers.metrics import record_tool_call

from code_agent.dependency import tracer
from pydantic import BaseModel, TypeAdapter
from typing import Iterable, Callable

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
    def register_tool(
        cls, name: str, description: str, param_type: type[BaseModel]
    ) -> Callable[[type[BaseTool]], type[BaseTool]]:
        """注册工具装饰器

        Args:
            name: 工具名称
            description: 工具描述
            param_type: 工具参数模型类

        Returns:
            工具类装饰器
        """

        def wrapper(tool_class: type[BaseTool]) -> type[BaseTool]:
            tool = tool_class()
            cls._registered_tools[name] = tool
            cls._build_tool_info(name, description, param_type)
            return tool_class

        return wrapper

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
    def _build_tool_info(cls, name: str, description: str, param_type: type[BaseModel]):
        """构建工具信息

        Returns:
            工具信息列表
        """

        tool_info: ChatCompletionFunctionToolParam = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": TypeAdapter(param_type).json_schema(mode="serialization"),
            },
        }
        cls._tools_info[name] = tool_info

    @classmethod
    @tracer.start_as_current_span("handle_tool_calls")
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
    @tracer.start_as_current_span("handle_function_tool_call")
    def handle_function_tool_call(
        cls, tool_call: ChatCompletionMessageFunctionToolCall
    ) -> ChatCompletionToolMessageParam:
        """处理工具调用"""
        tool = cls.get_tool(tool_call.function.name)
        if tool is None:
            record_tool_call(tool_call.function.name, 0.0, success=False)
            return {
                "content": "工具不存在",
                "role": "tool",
                "tool_call_id": tool_call.id,
            }
        record_tool_call(tool_call.function.name, 0.0, success=True)
        return {
            "content": tool.run(tool_call.function.arguments),
            "role": "tool",
            "tool_call_id": tool_call.id,
        }
