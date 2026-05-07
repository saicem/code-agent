#!/usr/bin/env python3
"""
工具模块
"""

import asyncio
import logging

from openai.types.chat import (
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionToolMessageParam,
)
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode

from code_agent.core.state import tracer
from code_agent.tools._manager import (
    ToolInfo,
    ToolRegistry,
    discover_tools,
    get_tool,
    invoke_tool,
    tools_for_gen_ai,
)
from code_agent.utils import print_tool_output
from code_agent.utils.tool_util import build_tool_response

# 自动发现并注册所有工具模块
discover_tools()

_logger = logging.getLogger(__name__)


@tracer.start_as_current_span("handle_tool_calls")
async def handle_tool_calls(
    tool_calls: list[ChatCompletionMessageToolCallUnion],
) -> list[ChatCompletionToolMessageParam]:
    """处理工具调用列表"""
    return await asyncio.gather(*[handle_function_tool_call(tool_call) for tool_call in tool_calls])


@tracer.start_as_current_span("handle_function_tool_call")
async def handle_function_tool_call(
    tool_call: ChatCompletionMessageToolCallUnion,
) -> ChatCompletionToolMessageParam:
    """处理单个工具调用"""
    if isinstance(tool_call, ChatCompletionMessageFunctionToolCall):
        tool_name = tool_call.function.name
        _logger.debug(f"执行工具调用: {tool_name}")

        tool_info = get_tool(tool_name)
        if tool_info is None:
            _logger.error(f"工具 {tool_name} 未找到或已禁用")
            return {
                "role": "tool",
                "content": build_tool_response(False, f"工具 {tool_name} 未找到或已禁用"),
                "tool_call_id": tool_call.id,
            }

        current_span = trace.get_current_span()
        current_span.set_attribute("tool.name", tool_name)

        try:
            _logger.debug(f"工具 {tool_name} 参数: {tool_call.function.arguments}")
            print_tool_output(tool_call.function.arguments, tool_name)
            content = await invoke_tool(tool_info, tool_call.function.arguments)
            _logger.debug(f"工具 {tool_name} 执行成功")
            current_span.set_status(StatusCode.OK)
        except Exception as e:
            _logger.error(f"工具 {tool_name} 执行失败: {e}", exc_info=True)
            current_span.set_status(StatusCode.ERROR, str(e))
            current_span.record_exception(e)
            content = str(e)

        return {
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call.id,
        }
    else:
        # 处理自定义工具调用（暂不支持）
        _logger.warning(f"不支持的工具调用类型: {type(tool_call)}")
        return {
            "role": "tool",
            "content": build_tool_response(False, "不支持的工具调用类型"),
            "tool_call_id": tool_call.id,
        }


__all__ = [
    "ToolInfo",
    "ToolRegistry",
    "get_tool",
    "handle_tool_calls",
    "invoke_tool",
    "tools_for_gen_ai",
]
