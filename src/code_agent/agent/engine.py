#!/usr/bin/env python3
"""
思考引擎模块
"""

import re

from dependency_injector.wiring import Provide, inject
from openai.types.chat import ChatCompletionMessageToolCallUnion
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode

from code_agent import monitoring
from code_agent.agent.gate import GenAiGate
from code_agent.agent.memory import save_compressed_data
from code_agent.agent.prompt import (
    COMPRESS_USER_CALL_MESSAGE,
)
from code_agent.agent.session import Session
from code_agent.core.config import get_config
from code_agent.core.container import Container
from code_agent.core.exceptions import SystemException
from code_agent.tools import (
    handle_tool_calls,
    tools_for_gen_ai,
)
from code_agent.utils import print_model_output, print_system_output

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)
_engine_config = get_config().engine


@_tracer.start_as_current_span("reasoning_acting")
async def reasoning_acting(session: Session, tag: str) -> None:
    try:
        await _reasoning_acting(session, tag)
    except Exception as e:
        _logger.error(f"ReAct 循环执行失败: {e}", exc_info=True)
        raise


@inject
async def _reasoning_acting(
    session: Session, tag: str, gate: GenAiGate = Provide[Container.gate]
) -> None:
    span = trace.get_current_span()
    span.set_attribute("gen_ai.tool.tag", tag)
    span.set_attribute("gen_ai.session_id", session.data.session_id)
    if session.data.parent_session_id is not None:
        span.set_attribute("gen_ai.parent_session_id", session.data.parent_session_id)
    _logger.info(f"开始 ReAct 循环，最大循环次数: {_engine_config.max_cycles}，工具标签: {tag}")
    cycle_count = 0
    while cycle_count < _engine_config.max_cycles:
        cycle_count += 1
        _logger.debug(f"第 {cycle_count + 1} 次循环")
        if session.data.total_token >= _engine_config.max_token:
            await _compress_session(session)
        response = await gate.call_model(session.data.messages, tools_for_gen_ai(tag))
        message = response.choices[0].message

        # 处理助手消息
        if message.content is not None:
            _logger.info(f"助手响应内容长度: {len(message.content)} 字符")
            session.add_assistant_message(message.content)
            tool_call_summary = _get_tool_summary(message.tool_calls) if message.tool_calls else ""
            print_model_output(message.content + tool_call_summary)

        if response.usage:
            session.data.total_token = response.usage.total_tokens

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
    session: Session,
) -> None:
    await reasoning_acting(session, "plan")


def _extract_xml_tags(content: str) -> dict[str, str]:
    """从内容中提取 XML 标签内容

    Args:
        content: 包含 XML 标签的内容

    Returns:
        包含各标签内容的字典
    """
    tags = ["user_preferences", "project_context", "current_task"]
    result: dict[str, str] = {}

    for tag in tags:
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            result[tag] = match.group(1).strip()
        else:
            result[tag] = ""

    return result


@_tracer.start_as_current_span("compress_session")
async def _compress_session(
    session: Session,
    gate: GenAiGate = Provide[Container.gate],
) -> None:
    print_system_output("压缩会话中...")
    span = trace.get_current_span()
    _logger.info(f"压缩会话: {session.data.session_id} 总token: {session.data.total_token}")
    session.add_user_message(COMPRESS_USER_CALL_MESSAGE)

    # 最多重试 3 次
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        if attempt > max_retries:
            span.set_status(StatusCode.ERROR, "压缩会话失败：返回内容为空")
            raise SystemException("压缩会话失败：返回内容为空")
        try:
            result = await gate.call_model(session.data.messages)
            compressed_content = result.choices[0].message.content

            if not compressed_content:
                _logger.error(f"会话压缩 {session.data.session_id} 失败: 返回内容为空")
                _logger.warning(f"第 {attempt} 次压缩失败，准备重试...")
                continue

            # 提取 XML 标签内容
            extracted_data = _extract_xml_tags(compressed_content)

            # 检查是否成功提取到所有标签
            missing_tags = [tag for tag, content in extracted_data.items() if not content]
            if missing_tags:
                _logger.warning(f"第 {attempt} 次压缩：缺少标签 {missing_tags}")

            # 保存用户偏好和项目情况到文件
            save_compressed_data(
                extracted_data["user_preferences"],
                extracted_data["project_context"],
            )

            # 更新会话
            session.clear_message()
            session.add_user_message(compressed_content)

            if result.usage:
                session.data.total_token = result.usage.completion_tokens
                span.add_event(
                    "context_compressed",
                    {
                        "gen_ai.token.original": result.usage.prompt_tokens,
                        "gen_ai.token.compressed": result.usage.completion_tokens,
                        "gen_ai.session_id": session.data.session_id,
                    },
                )

            _logger.info(f"会话 {session.data.session_id} 压缩完成")
            print_system_output("压缩会话完成")
            break

        except Exception as e:
            _logger.error(f"第 {attempt} 次压缩异常: {e}", exc_info=True)
            if attempt == max_retries:
                span.set_status(StatusCode.ERROR, f"压缩会话失败: {e}")
                raise SystemException(f"压缩会话失败: {e}") from None


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
