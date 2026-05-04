#!/usr/bin/env python3
"""
工具模块
包含各种工具的定义和实现
"""

from openai.types.chat import (
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionToolMessageParam,
)
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode

from code_agent.core.di import container
from code_agent.tools import (
    bash_tool,
    edit_tool,
    glob_tool,
    grep_tool,
    read_tool,
    search_tool,
    time_tool,
    write_tool,
)
from code_agent.tools._manager import get_tool as _get_tool
from code_agent.tools._manager import tools_for_gen_ai

__all__ = [
    "bash_tool",
    "edit_tool",
    "get_tool",
    "glob_tool",
    "grep_tool",
    "read_tool",
    "search_tool",
    "time_tool",
    "tools_for_gen_ai",
    "write_tool",
]


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
    current_span = trace.get_current_span()
    tool_name = tool_call.function.name
    current_span.set_attributes(
        {
            "tool.name": tool_name,
            "tool.call_id": tool_call.id,
            "tool.arguments": tool_call.function.arguments,
        }
    )

    tool_info = _get_tool(tool_name)
    if tool_info is None:
        current_span.set_status(StatusCode.ERROR, "工具不存在")
        return {
            "content": "工具不存在",
            "role": "tool",
            "tool_call_id": tool_call.id,
        }

    try:
        if tool_info.is_async:
            content = await tool_info.func(tool_call.function.arguments)
        else:
            content = tool_info.func(tool_call.function.arguments)
        current_span.set_status(StatusCode.OK)
    except Exception as e:
        current_span.set_status(StatusCode.ERROR, str(e))
        raise

    return {
        "content": content,
        "role": "tool",
        "tool_call_id": tool_call.id,
    }
