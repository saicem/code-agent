#!/usr/bin/env python3
"""
Code Agent 类
"""

import logging

from code_agent.session import Session
from code_agent.dependency import CONFIG
from openai import OpenAI
from code_agent.tools.tool_manager import ToolManager
from opentelemetry import trace

tracer = trace.get_tracer("agent")
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
        logger.debug(f"开始执行任务, 会话ID: {session.session_id}")

        try:
            # ReAct 循环
            cycle_count = 0
            logger.info(f"开始 ReAct 循环，最大循环次数: {CONFIG.react_max_cycles}")

            while cycle_count < CONFIG.react_max_cycles:
                logger.debug(f"第 {cycle_count + 1} 次循环")

                # 调用模型
                logger.debug("调用 OpenAI API...")
                response = self.client.chat.completions.create(
                    model=CONFIG.model,
                    messages=session.messages_for_model(),
                    tools=ToolManager.tools_for_model(),
                )
                logger.debug("OpenAI API 调用完成")

                message = response.choices[0].message

                if message.content is not None:
                    logger.info(f"助手响应内容长度: {len(message.content)} 字符")
                    print(f"助手消息: {message.content}")
                    session.add_assistant_message(message.content)

                if message.tool_calls is None or len(message.tool_calls) == 0:
                    logger.info("没有工具调用，任务结束")
                    print("没有工具调用，任务结束")
                    break
                else:
                    tool_calls = message.tool_calls
                    logger.info(f"工具调用数量: {len(tool_calls)}")
                    print(f"工具调用: {tool_calls}")

                    tool_call_result = ToolManager.handle_tool_calls(tool_calls)
                    logger.debug(f"工具调用结果: {tool_call_result}")
                    print(f"工具调用结果: {tool_call_result}")
                    session.add_tool_messages(tool_call_result)

                cycle_count += 1

            if cycle_count >= CONFIG.react_max_cycles:
                logger.warning(f"达到最大循环次数 {CONFIG.react_max_cycles}")
                return f"执行异常: 达到最大循环次数 {CONFIG.react_max_cycles}"
            else:
                logger.info(f"任务完成，共执行 {cycle_count} 次循环")
                return "任务结束"

        except Exception as e:
            error_message = str(e)
            logger.error(f"执行任务失败: {error_message}", exc_info=True)
            return f"执行错误: {error_message}"
