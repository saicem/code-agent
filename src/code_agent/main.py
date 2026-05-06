#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

import asyncio

from dependency_injector.wiring import Provide, inject

import code_agent._setup  # noqa: F401
from code_agent.agent.engine import reasoning_acting
from code_agent.agent.session_manager import SessionManager
from code_agent.commands import handle_command
from code_agent.core.container import Container
from code_agent.core.state import current_session
from code_agent.monitoring import get_logger, get_tracer
from code_agent.utils import get_user_input, print_system_output

_logger = get_logger(__name__)
_tracer = get_tracer(__name__)


@inject
async def main(session_manager: SessionManager = Provide[Container.session_manager]):
    _logger.info("========== Code Agent 启动中 ==========")

    session = session_manager.load_last_session()
    if not session:
        session = session_manager.create_session()
    current_session.set(session)
    print_system_output("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令", "info")

    # 循环对话
    while True:
        task = get_user_input("\n任务: ")

        if task.strip() == "":
            continue

        # 处理命令
        if task.startswith("/"):
            handle_command(task)
            continue

        # 执行任务
        session = current_session.get()
        session.add_user_message(task)
        try:
            # 从依赖容器获取推理引擎
            await reasoning_acting(session, "code")
        except Exception as e:
            _logger.error(f"任务执行失败: {e}", exc_info=True)
            print_system_output(f"执行错误: {e}", "error")
            continue

        session_manager.save_session(session)


if __name__ == "__main__":
    container = Container()
    # Wire 所有相关的子包和模块
    container.wire(modules=[__name__], packages=["code_agent"])
    asyncio.run(main())
