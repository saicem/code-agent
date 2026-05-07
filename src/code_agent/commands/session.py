from dependency_injector.wiring import Provide

from code_agent.agent.session_manager import SessionManager
from code_agent.core.container import Container
from code_agent.core.state import current_session
from code_agent.utils import print_system_output


def _show_session_help() -> None:
    print_system_output("\n会话管理指令:", "info")
    print_system_output("  /session list      - 列出所有会话", "info")
    print_system_output("  /session switch <id> - 切换到指定会话", "info")
    print_system_output("  /session new       - 创建新会话", "info")
    print_system_output("  /session delete <id> - 删除指定会话", "info")
    print_system_output("  /session info      - 显示当前会话信息", "info")


def _handle_session_list(
    session_manager: SessionManager = Provide[Container.session_manager],
) -> None:
    sessions = session_manager.get_session_list()
    if not sessions:
        print_system_output("\n没有找到任何会话", "info")
        return

    print_system_output("\n会话列表:", "info")
    current_id = current_session.get().session_id
    for i, session in enumerate(sessions, 1):
        marker = "*" if session["id"] == current_id else " "
        created = session.get("created_at", "")[:19].replace("T", " ")
        updated = session.get("updated_at", "")[:19].replace("T", " ")
        print_system_output(f"  {marker}{i}. {session['id']}", "info")
        print_system_output(f"       创建: {created}", "info")
        print_system_output(f"       更新: {updated}", "info")
        print_system_output(f"       消息: {session['message_count']} 条", "info")


def _handle_session_switch(
    session_id: str, session_manager: SessionManager = Provide[Container.session_manager]
) -> None:
    session = session_manager.load_session(session_id)
    if session:
        current_session.set(session)
        print_system_output(f"\n已切换到会话: {session_id}", "info")
    else:
        print_system_output(f"\n错误: 无法找到会话 {session_id}", "error")


def _handle_session_new(
    session_manager: SessionManager = Provide[Container.session_manager],
) -> None:
    session = session_manager.create_session()
    current_session.set(session)
    print_system_output(f"\n已创建新会话: {session.session_id}", "info")


def _handle_session_delete(
    session_id: str,
    session_manager: SessionManager = Provide[Container.session_manager],
) -> None:
    if session_manager.delete_session(session_id):
        print_system_output(f"\n已删除会话: {session_id}", "info")
        if current_session.get().session_id == session_id:
            session = session_manager.create_session()
            current_session.set(session)
            print_system_output(f"已创建新会话: {session.session_id}", "info")
    else:
        print_system_output(f"\n错误: 无法找到会话 {session_id}", "error")


def _handle_session_info() -> None:
    session = current_session.get()
    print_system_output("\n当前会话信息:", "info")
    print_system_output(f"  会话ID: {session.session_id}", "info")
    print_system_output(f"  创建时间: {session.created_at[:19].replace('T', ' ')}", "info")
    print_system_output(f"  更新时间: {session.updated_at[:19].replace('T', ' ')}", "info")
    print_system_output(f"  消息数量: {len(session.messages)}", "info")
    print_system_output(f"  预估总Token数: {session.total_token}", "info")


def _handle_session(command: str) -> None:
    cmd_parts = command.split(" ", 2)
    if len(cmd_parts) < 2:
        _show_session_help()
        return

    sub_cmd = cmd_parts[1].lower()

    if sub_cmd == "list":
        _handle_session_list()
    elif sub_cmd == "switch":
        if len(cmd_parts) < 3:
            print_system_output("\n用法: /session switch <会话ID>", "info")
            return
        session_id = cmd_parts[2].strip()
        _handle_session_switch(session_id)
    elif sub_cmd == "new":
        _handle_session_new()
    elif sub_cmd == "delete":
        if len(cmd_parts) < 3:
            print_system_output("\n用法: /session delete <会话ID>", "info")
            return
        session_id = cmd_parts[2].strip()
        _handle_session_delete(session_id)
    elif sub_cmd == "info":
        _handle_session_info()
    else:
        _show_session_help()


def register_session_commands(handler) -> None:
    handler.register_command("/session", _handle_session, "会话管理")
