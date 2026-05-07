import logging

from dependency_injector.wiring import Provide, inject

from code_agent.agent.engine import reasoning_acting
from code_agent.agent.session_manager import SessionManager
from code_agent.commands import handle_command
from code_agent.core.container import Container
from code_agent.core.state import current_session
from code_agent.utils import get_user_input, print_system_output

_logger = logging.getLogger(__name__)


@inject
def init_current_session(
    session_manager: SessionManager = Provide[Container.session_manager],
) -> None:
    session = session_manager.load_last_session()
    if not session:
        session = session_manager.create_session()
    current_session.set(session)


def must_get_user_input() -> str:
    while True:
        task = get_user_input("\n任务: ")
        if task.strip() == "":
            continue
        return task


@inject
async def handle_task(
    task: str, session_manager: SessionManager = Provide[Container.session_manager]
) -> None:
    session = current_session.get()
    session.add_user_message(task)
    try:
        await reasoning_acting(session, "code")
    except Exception as e:
        _logger.error(f"任务执行失败: {e}", exc_info=True)
        print_system_output(f"执行错误: {e}", "error")
        raise e
    session_manager.save_session(session)


async def start_agent():
    _logger.info("========== Code Agent 启动中 ==========")
    init_current_session()
    print_system_output("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令", "info")

    # 循环对话
    while True:
        user_msg = must_get_user_input()
        if user_msg.startswith("/"):
            handle_command(user_msg)
        else:
            await handle_task(user_msg)
