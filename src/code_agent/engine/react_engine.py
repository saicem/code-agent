#!/usr/bin/env python3
"""
ReAct 引擎模块
负责执行异步 ReAct 推理循环
"""

import logging
import time
from typing import List, Any

from openai import AsyncOpenAI
from opentelemetry import trace

from code_agent.core.session import Session
from code_agent.core.di import container
from code_agent.tools.tool_manager import (
    handle_function_tool_call,
    tools_for_model,
)
from code_agent.monitoring.metrics import (
    record_model_call,
    record_tool_call,
    record_react_cycles,
    record_message,
)

tracer = trace.get_tracer("react_engine")
logger = logging.getLogger(__name__)


class ReActEngine:
    """ReAct 推理引擎（异步版本）"""

    def __init__(self, client: AsyncOpenAI):
        """初始化 ReAct 引擎

        Args:
            client: 异步 OpenAI 客户端实例
        """
        self.client = client
        self.config = container.config

    @tracer.start_as_current_span("react_loop")
    async def execute(self, session: Session) -> str:
        """执行异步 ReAct 推理循环

        Args:
            session: 会话对象

        Returns:
            执行结果
        """
        logger.info(f"开始 ReAct 循环，最大循环次数: {self.config.react_max_cycles}")

        cycle_count = 0
        while cycle_count < self.config.react_max_cycles:
            logger.debug(f"第 {cycle_count + 1} 次循环")

            # 异步调用模型
            response, api_duration = await self._call_model(session)

            # 处理响应
            if not await self._handle_response(session, response, api_duration):
                break

            cycle_count += 1

        record_react_cycles(cycle_count)

        if cycle_count >= self.config.react_max_cycles:
            logger.warning(f"达到最大循环次数 {self.config.react_max_cycles}")
            return f"执行异常: 达到最大循环次数 {self.config.react_max_cycles}"
        else:
            logger.info(f"任务完成，共执行 {cycle_count} 次循环")
            return "任务结束"

    async def _call_model(self, session: Session) -> tuple[Any, float]:
        """异步调用模型

        Args:
            session: 会话对象

        Returns:
            (响应对象, 耗时)
        """
        logger.debug("异步调用 OpenAI API...")
        api_start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=session.messages_for_model(),
            tools=tools_for_model(),
        )

        api_duration = time.time() - api_start_time
        logger.debug("异步 OpenAI API 调用完成")

        return response, api_duration

    async def _handle_response(
        self, session: Session, response: Any, api_duration: float
    ) -> bool:
        """处理模型响应

        Args:
            session: 会话对象
            response: 模型响应
            api_duration: API调用耗时

        Returns:
            True: 继续循环, False: 结束循环
        """
        # 记录模型调用指标
        usage = response.usage
        if usage:
            record_model_call(
                model=self.config.model,
                duration=api_duration,
                success=True,
                total_tokens=usage.total_tokens,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        else:
            record_model_call(
                model=self.config.model, duration=api_duration, success=True
            )

        message = response.choices[0].message

        # 处理助手消息
        if message.content is not None:
            logger.info(f"助手响应内容长度: {len(message.content)} 字符")
            print(f"助手消息: {message.content}")
            session.add_assistant_message(message.content)
            record_message("assistant")

        # 检查是否有工具调用
        if message.tool_calls is None or len(message.tool_calls) == 0:
            logger.info("没有工具调用，任务结束")
            print("没有工具调用，任务结束")
            return False

        # 处理工具调用
        await self._handle_tool_calls(session, message.tool_calls)
        return True

    async def _handle_tool_calls(self, session: Session, tool_calls: List[Any]):
        """异步处理工具调用

        Args:
            session: 会话对象
            tool_calls: 工具调用列表
        """
        logger.info(f"工具调用数量: {len(tool_calls)}")
        print(f"工具调用: {tool_calls}")

        tool_start_time = time.time()
        tool_call_result = await handle_function_tool_call(tool_calls[0])
        tool_duration = time.time() - tool_start_time

        logger.debug(f"工具调用结果: {tool_call_result}")
        print(f"工具调用结果: {tool_call_result}")
        session.add_tool_messages([tool_call_result])

        # 记录工具调用指标
        for tool_call in tool_calls:
            tool_name = str(tool_call)
            if hasattr(tool_call, "function"):
                func = getattr(tool_call, "function", None)
                if func and hasattr(func, "name"):
                    tool_name = getattr(func, "name", str(tool_call))
            record_tool_call(tool_name, tool_duration, success=True)
