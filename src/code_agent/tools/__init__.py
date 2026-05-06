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
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace.status import StatusCode

from code_agent.monitoring import get_logger, get_tracer
from code_agent.tools import (
    bash_tool,
    edit_tool,
    glob_tool,
    grep_tool,
    read_tool,
    search_tool,
    sub_agent_tool,
    time_tool,
    write_tool,
)
from code_agent.tools._manager import get_tool as _get_tool
from code_agent.tools._manager import tools_for_gen_ai
from code_agent.utils import print_tool_output

__all__ = [
    "bash_tool",
    "edit_tool",
    "get_tool",
    "glob_tool",
    "grep_tool",
    "read_tool",
    "search_tool",
    "sub_agent_tool",
    "time_tool",
    "tools_for_gen_ai",
    "write_tool",
]


_tracer = get_tracer(__name__)
_logger = get_logger(__name__)


@_tracer.start_as_current_span("handle_tool_calls")
async def handle_tool_calls(
    tool_calls: list[ChatCompletionMessageToolCallUnion],
) -> list[ChatCompletionToolMessageParam]:
    """处理多个工具调用"""
    _logger.info(f"开始处理 {len(tool_calls)} 个工具调用")
    from typing import cast

    result: list[ChatCompletionToolMessageParam] = []
    for i, tool_call in enumerate(tool_calls):
        if tool_call.type == "custom":
            _logger.debug(f"跳过自定义工具调用 #{i}")
            continue
        func_call = cast(ChatCompletionMessageFunctionToolCall, tool_call)
        _logger.debug(f"处理工具调用 #{i}: {func_call.function.name}")
        result.append(await handle_function_tool_call(func_call))
    _logger.info(f"工具调用处理完成，共 {len(result)} 个结果")
    return result


@_tracer.start_as_current_span("handle_function_tool_call")
async def handle_function_tool_call(
    tool_call: ChatCompletionMessageFunctionToolCall,
) -> ChatCompletionToolMessageParam:
    """处理单个工具调用"""
    current_span = trace.get_current_span()
    tool_name = tool_call.function.name
    _logger.debug(f"调用工具: {tool_name}, call_id: {tool_call.id}")

    current_span.set_attributes(
        {
            gen_ai_attributes.GEN_AI_OPERATION_NAME: gen_ai_attributes.GenAiOperationNameValues.EXECUTE_TOOL.value,
            "gen_ai.tool.name": tool_name,
            "gen_ai.tool.call_id": tool_call.id,
            "gen_ai.tool.arguments": tool_call.function.arguments,
        }
    )

    tool_info = _get_tool(tool_name)
    if tool_info is None:
        _logger.error(f"工具不存在: {tool_name} {tool_call}")
        current_span.set_status(StatusCode.ERROR, "工具不存在")
        return {
            "content": "工具不存在",
            "role": "tool",
            "tool_call_id": tool_call.id,
        }

    try:
        _logger.debug(f"工具 {tool_name} 参数: {tool_call.function.arguments}")
        print_tool_output(tool_call.function.arguments, tool_name)
        if tool_info.is_async:
            content = await tool_info.func(tool_call.function.arguments)
        else:
            content = tool_info.func(tool_call.function.arguments)
        _logger.debug(f"工具 {tool_name} 执行成功")
        current_span.set_status(StatusCode.OK)
    except Exception as e:
        _logger.error(f"工具 {tool_name} 执行失败: {e}", exc_info=True)
        current_span.set_status(StatusCode.ERROR, str(e))
        current_span.record_exception(e)
        content = str(e)

    print_tool_output(content, tool_name)

    return {
        "content": content,
        "role": "tool",
        "tool_call_id": tool_call.id,
    }
