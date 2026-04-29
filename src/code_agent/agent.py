#!/usr/bin/env python3
"""
Code Agent 类
"""

from code_agent.session import Session

from code_agent.dependency import CONFIG

from openai import OpenAI
from code_agent.tools.tool_manager import ToolManager


class CodeAgent:
    """Code Agent 类"""

    def __init__(self, api_key: str, base_url: str | None = None):
        """初始化 Code Agent

        Args:
            api_key: API 密钥
            base_url: 基础 URL（可选）
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def execute_task(self, session: Session) -> str:
        """执行任务

        Args:
            session: 会话对象

        Returns:
            执行结果
        """
        try:
            # ReAct 循环
            cycle_count = 0
            while cycle_count < CONFIG.react_max_cycles:
                response = self.client.chat.completions.create(
                    model=CONFIG.model,
                    messages=session.messages_for_model(),
                    tools=ToolManager.tools_for_model(),
                )

                message = response.choices[0].message
                if message.tool_calls is None or len(message.tool_calls) == 0:
                    print(f"助手消息: {message.content}")
                    break
                else:
                    tool_calls = message.tool_calls
                    tool_call_result = ToolManager.handle_tool_calls(tool_calls)
                    session.add_tool_messages(tool_call_result)
                cycle_count += 1

            # 循环次数超过限制
            return f"执行超时: 达到最大循环次数 {CONFIG.react_max_cycles}"

        except Exception as e:
            error_message = str(e)
            return f"执行错误: {error_message}"
