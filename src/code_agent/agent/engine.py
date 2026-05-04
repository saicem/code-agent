#!/usr/bin/env python3
"""
思考引擎模块
"""

from code_agent import monitoring
from code_agent.agent.gate import ModelGate
from code_agent.core.config import ReactConfig
from code_agent.core.session import Session
from code_agent.tools import (
    handle_tool_calls,
    tools_for_gen_ai,
)

_tracer = monitoring.get_tracer("react_engine")
_logger = monitoring.get_logger(__name__)


@_tracer.start_as_current_span("react_loop")
async def execute_reasoning_acting(gate: ModelGate, session: Session, config: ReactConfig) -> None:
    _logger.info(f"开始 ReAct 循环，最大循环次数: {config.max_cycles}")
    cycle_count = 0
    while cycle_count < config.max_cycles:
        cycle_count += 1
        _logger.debug(f"第 {cycle_count + 1} 次循环")

        response = await gate.call_model(session.messages, tools_for_gen_ai())
        message = response.choices[0].message

        # 处理助手消息
        if message.content is not None:
            _logger.info(f"助手响应内容长度: {len(message.content)} 字符")
            session.add_assistant_message(message.content)
            print(f"助手:{message.content}")

        # 处理工具调用
        if message.tool_calls is None:
            _logger.info(f"任务完成，共执行 {cycle_count} 次循环")
            return
        else:
            tool_call_result = await handle_tool_calls(message.tool_calls)
            session.add_tool_messages(tool_call_result)

        if cycle_count >= config.max_cycles:
            _logger.warning(f"达到最大循环次数 {config.max_cycles}")
            return
