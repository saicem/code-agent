#!/usr/bin/env python3
"""
Code Agent 类
"""

import logging
import time
from code_agent.helpers.metrics import (
    record_task_start,
    record_task_completion,
    record_model_call,
    record_tool_call,
    record_react_cycles,
    record_message,
)
from code_agent.session import Session
from code_agent.dependency import CONFIG, tracer
from openai import OpenAI
from code_agent.tools.tool_manager import ToolManager

logger = logging.getLogger()


class CodeAgent:
    """Code Agent 类"""

    def __init__(self, api_key: str, base_url: str | None = None):
        """初始化 Code Agent

        Args:
            api_key: API 密钥
            base_url: 基础 URL（可选）
        """
        logger.debug(f"初始化 CodeAgent, base_url: {base_url}")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info("CodeAgent 初始化完成")

    @tracer.start_as_current_span("execute_task")
    def execute_task(self, session: Session) -> str:
        """执行任务

        Args:
            session: 会话对象

        Returns:
            执行结果
        """
        task_start_time = time.time()
        logger.debug(f"开始执行任务, 会话ID: {session.session_id}")
        record_task_start()

        try:
            # ReAct 循环
            cycle_count = 0
            logger.info(f"开始 ReAct 循环，最大循环次数: {CONFIG.react_max_cycles}")

            while cycle_count < CONFIG.react_max_cycles:
                logger.debug(f"第 {cycle_count + 1} 次循环")

                # 调用模型
                logger.debug("调用 OpenAI API...")
                api_start_time = time.time()
                response = self.client.chat.completions.create(
                    model=CONFIG.model,
                    messages=session.messages_for_model(),
                    tools=ToolManager.tools_for_model(),
                )
                api_duration = time.time() - api_start_time
                logger.debug("OpenAI API 调用完成")

                # 记录模型调用指标
                usage = response.usage
                if usage:
                    record_model_call(
                        model=CONFIG.model,
                        duration=api_duration,
                        success=True,
                        total_tokens=usage.total_tokens,
                        prompt_tokens=usage.prompt_tokens,
                        completion_tokens=usage.completion_tokens,
                    )
                else:
                    record_model_call(
                        model=CONFIG.model, duration=api_duration, success=True
                    )

                message = response.choices[0].message

                if message.content is not None:
                    logger.info(f"助手响应内容长度: {len(message.content)} 字符")
                    print(f"助手消息: {message.content}")
                    session.add_assistant_message(message.content)
                    record_message("assistant")

                if message.tool_calls is None or len(message.tool_calls) == 0:
                    logger.info("没有工具调用，任务结束")
                    print("没有工具调用，任务结束")
                    break
                else:
                    tool_calls = message.tool_calls
                    logger.info(f"工具调用数量: {len(tool_calls)}")
                    print(f"工具调用: {tool_calls}")

                    tool_start_time = time.time()
                    tool_call_result = ToolManager.handle_tool_calls(tool_calls)
                    tool_duration = time.time() - tool_start_time
                    logger.debug(f"工具调用结果: {tool_call_result}")
                    print(f"工具调用结果: {tool_call_result}")
                    session.add_tool_messages(tool_call_result)

                    # 记录工具调用指标
                    for tool_call in tool_calls:
                        tool_name = str(tool_call)
                        if hasattr(tool_call, "function"):
                            func = getattr(tool_call, "function", None)
                            if func and hasattr(func, "name"):
                                tool_name = getattr(func, "name", str(tool_call))
                        record_tool_call(tool_name, tool_duration, success=True)

                cycle_count += 1

            task_duration = time.time() - task_start_time

            if cycle_count >= CONFIG.react_max_cycles:
                logger.warning(f"达到最大循环次数 {CONFIG.react_max_cycles}")
                record_task_completion(
                    success=False, duration=task_duration, steps=cycle_count
                )
                return f"执行异常: 达到最大循环次数 {CONFIG.react_max_cycles}"
            else:
                logger.info(f"任务完成，共执行 {cycle_count} 次循环")
                record_react_cycles(cycle_count)
                record_task_completion(
                    success=True, duration=task_duration, steps=cycle_count
                )
                return "任务结束"

        except Exception as e:
            task_duration = time.time() - task_start_time
            error_message = str(e)
            logger.error(f"执行任务失败: {error_message}", exc_info=True)
            record_task_completion(success=False, duration=task_duration)
            return f"执行错误: {error_message}"
