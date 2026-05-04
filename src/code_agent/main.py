#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

import asyncio

import code_agent._setup  # noqa: F401
from code_agent.agent import prompt
from code_agent.agent.engine import execute_reasoning_acting
from code_agent.agent.gate import ModelGate
from code_agent.commands import handle_command
from code_agent.core.config import get_config
from code_agent.core.di import container
from code_agent.core.session_manager import current_session
from code_agent.monitoring import get_logger, get_tracer

_logger = get_logger(__name__)
_tracer = get_tracer(__name__)


async def main():
    _logger.info("========== Code Agent 启动中 ==========")
    config = get_config()

    session = container.session_manager.load_last_session()
    if not session:
        session = container.session_manager.create_session()
    current_session.set(session)

    print("记忆摘要:")
    print(container.memory_manager.get_summary())
    print("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令")

    gate = ModelGate(config.gate)

    # 循环对话
    while True:
        task = input("\n任务: ")

        if task.strip() == "":
            continue

        # 处理命令
        if handle_command(task):
            continue

        # 执行任务
        session = current_session.get()
        session.set_system_prompt(prompt.code_system)
        session.add_user_message(task)

        try:
            await execute_reasoning_acting(gate, session, config.react)
        except Exception as e:
            _logger.error(f"任务执行失败: {e}", exc_info=True)
            print(f"执行错误: {e}")
            continue

        container.session_manager.save_session(session)


if __name__ == "__main__":
    asyncio.run(main())
