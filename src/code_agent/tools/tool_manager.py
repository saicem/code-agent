#!/usr/bin/env python3
"""
工具管理模块
支持异步工具调用
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from code_agent.monitoring.metrics import record_tool_call
from code_agent.core.di import container
from pydantic import BaseModel, TypeAdapter

from openai.types.chat import (
    ChatCompletionToolUnionParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionToolMessageParam,
)


@dataclass
class ToolInfo:
    """工具信息"""

    func: Callable[..., Any]
    is_async: bool


_registered_tools: dict[str, ToolInfo] = {}
_tools_info: dict[str, ChatCompletionToolUnionParam] = {}


def register_tool(
    name: str, description: str, param_type: type[BaseModel]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = asyncio.iscoroutinefunction(func)
        _registered_tools[name] = ToolInfo(
            func=func,
            is_async=is_async,
        )
        _tools_info[name] = _build_tool_info(name, description, param_type)
        return func

    return wrapper


def get_tool(tool_name: str) -> ToolInfo | None:
    """获取工具信息

    Args:
        tool_name: 工具名称

    Returns:
        工具信息或 None
    """
    return _registered_tools.get(tool_name)


def tools_for_model() -> Iterable[ChatCompletionToolUnionParam]:
    """获取所有注册的工具信息

    Returns:
        工具信息列表
    """
    return _tools_info.values()


def _build_tool_info(
    name: str, description: str, param_type: type[BaseModel]
) -> ChatCompletionFunctionToolParam:
    """构建工具信息

    Returns:
        工具信息列表
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": TypeAdapter(param_type).json_schema(mode="serialization"),
        },
    }


@container.tracer.start_as_current_span("handle_tool_calls")
async def handle_tool_calls(
    tool_calls: list[ChatCompletionMessageToolCallUnion],
) -> list[ChatCompletionToolMessageParam]:
    from typing import cast

    result: list[ChatCompletionToolMessageParam] = []
    for tool_call in tool_calls:
        if tool_call.type == "custom":
            continue
        func_call = cast(ChatCompletionMessageFunctionToolCall, tool_call)
        result.append(await handle_function_tool_call(func_call))
    return result


@container.tracer.start_as_current_span("handle_function_tool_call")
async def handle_function_tool_call(
    tool_call: ChatCompletionMessageFunctionToolCall,
) -> ChatCompletionToolMessageParam:
    """处理工具调用"""
    from opentelemetry import trace

    current_span = trace.get_current_span()
    tool_name = tool_call.function.name
    current_span.set_attributes(
        {
            "tool.name": tool_name,
            "tool.call_id": tool_call.id,
            "tool.arguments": tool_call.function.arguments,
        }
    )

    tool_info = get_tool(tool_name)
    if tool_info is None:
        current_span.set_attribute("tool.success", False)
        current_span.set_attribute("tool.error", "工具不存在")
        record_tool_call(tool_name, 0.0, success=False)
        return {
            "content": "工具不存在",
            "role": "tool",
            "tool_call_id": tool_call.id,
        }

    tool_start_time = time.time()

    try:
        if tool_info.is_async:
            content = await tool_info.func(tool_call.function.arguments)
        else:
            content = tool_info.func(tool_call.function.arguments)
        current_span.set_attribute("tool.success", True)
        tool_duration = time.time() - tool_start_time
        record_tool_call(tool_name, tool_duration, success=True)
    except Exception as e:
        current_span.set_attribute("tool.success", False)
        current_span.set_attribute("tool.error", str(e))
        tool_duration = time.time() - tool_start_time
        record_tool_call(tool_name, tool_duration, success=False)
        raise

    return {
        "content": content,
        "role": "tool",
        "tool_call_id": tool_call.id,
    }
