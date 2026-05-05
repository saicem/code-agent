#!/usr/bin/env python3
"""
思考引擎模块
"""

from openai.types.chat import ChatCompletionMessageToolCallUnion
from opentelemetry import trace

from code_agent import monitoring
from code_agent.agent.gate import GenAiGate
from code_agent.agent.prompt import (
    COMPRESS_SYSTEM,
    COMPRESS_USER_CALL_MESSAGE,
)
from code_agent.core.config import get_config
from code_agent.core.session import Session
from code_agent.tools import (
    handle_tool_calls,
    tools_for_gen_ai,
)
from code_agent.tools._manager import TOOL_TAG_PLAN
from code_agent.utils import print_model_output

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)
_engine_config = get_config().engine


@_tracer.start_as_current_span("reasoning_acting")
async def reasoning_acting(gate: GenAiGate, session: Session, tag: str) -> None:
    span = trace.get_current_span()
    span.set_attribute("gen_ai.tool.tag", tag)
    _logger.info(f"开始 ReAct 循环，最大循环次数: {_engine_config.max_cycles}，工具标签: {tag}")
    cycle_count = 0
    while cycle_count < _engine_config.max_cycles:
        cycle_count += 1
        _logger.debug(f"第 {cycle_count + 1} 次循环")
        if session.data.total_token >= _engine_config.max_token:
            await _compress_session(session, gate)
        response = await gate.call_model(session.data.messages, tools_for_gen_ai(tag))
        message = response.choices[0].message

        # 处理助手消息
        if message.content is not None:
            _logger.info(f"助手响应内容长度: {len(message.content)} 字符")
            session.add_assistant_message(message.content)
            tool_call_summary = _get_tool_summary(message.tool_calls) if message.tool_calls else ""
            print_model_output(message.content + tool_call_summary)

        # 处理工具调用
        if message.tool_calls is None:
            _logger.info(f"任务完成，共执行 {cycle_count} 次循环")
            return
        else:
            tool_call_result = await handle_tool_calls(message.tool_calls)
            session.add_tool_messages(tool_call_result)

        if cycle_count >= _engine_config.max_cycles:
            _logger.warning(f"达到最大循环次数 {_engine_config.max_cycles}")
            return


@_tracer.start_as_current_span("plan_and_execute")
async def plan_and_execute(
    gate: GenAiGate,
    session: Session,
) -> None:
    await reasoning_acting(gate, session, TOOL_TAG_PLAN)


async def _compress_session(session: Session, gate: GenAiGate) -> None:
    _logger.info(f"压缩会话: {session.data.session_id} 总token: {session.data.total_token}")
    old_system_prompt = session.data.system_prompt
    session.set_system_prompt(COMPRESS_SYSTEM)
    session.add_user_message(COMPRESS_USER_CALL_MESSAGE)
    result = await gate.call_model(session.data.messages)
    compressed_content = result.choices[0].message.content
    if compressed_content:
        session.clear_message()
        session.add_user_message(compressed_content)
        session.set_system_prompt(old_system_prompt)
        _logger.info(f"会话 {session.data.session_id} 压缩完成")
    else:
        _logger.error(f"会话压缩 {session.data.session_id} 失败")
        raise ValueError("压缩会话失败")


def _get_tool_summary(tool_calls: list[ChatCompletionMessageToolCallUnion]) -> str:
    tool_call_summary = ""
    if tool_calls is not None:
        tool_call_names = []
        for tool_call in tool_calls:
            func = getattr(tool_call, "function", None)
            if func is not None:
                name = getattr(func, "name", None)
                if name:
                    tool_call_names.append(name)
            else:
                # Custom tool call
                tool_type = getattr(tool_call, "type", None)
                if tool_type:
                    tool_call_names.append(f"custom_{tool_type}")
        if tool_call_names:
            tool_call_summary = f"工具调用: {tool_call_names}"
    return tool_call_summary
