#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

from code_agent.agent.engine import execute_reasoning_acting

from code_agent.agent.gate import ModelGate
from code_agent.agent import prompt
from code_agent.core.session_manager import current_session
from code_agent import monitoring
from code_agent.core.di import container
import asyncio

_logger = monitoring.get_logger(__name__)
_tracer = monitoring.get_tracer(__name__)


async def main():
    if container.config.logging.otlp_enabled:
        monitoring.init()
    logger = monitoring.get_logger(__name__)
    logger.info("========== Code Agent 启动中 ==========")

    session = container.session_manager.load_last_session()
    if not session:
        session = container.session_manager.create_session()
    current_session.set(session)

    print("记忆摘要:")
    print(container.memory_manager.get_summary())
    print("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令")

    gate = ModelGate(container.config.gate)

    # 循环对话
    while True:
        task = input("\n任务: ")

        if task.strip() == "":
            continue

        # 处理命令
        if container.command_handler.handle_command(task):
            continue

        # 执行任务
        session = current_session.get()
        session.set_system_prompt(prompt.code_system)
        session.add_user_message(task)

        try:
            await execute_reasoning_acting(gate, session, container.config.react)
        except Exception as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            print(f"执行错误: {e}")
            continue

        container.session_manager.save_session(session)


if __name__ == "__main__":
    asyncio.run(main())
