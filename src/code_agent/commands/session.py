from code_agent.core.session_manager import SessionManager, current_session


def _show_session_help() -> None:
    print("\n会话管理指令:")
    print("  /session list      - 列出所有会话")
    print("  /session switch <id> - 切换到指定会话")
    print("  /session new       - 创建新会话")
    print("  /session delete <id> - 删除指定会话")
    print("  /session info      - 显示当前会话信息")


def _handle_session_list(session_manager: SessionManager) -> None:
    sessions = session_manager.get_session_list()
    if not sessions:
        print("\n没有找到任何会话")
        return

    print("\n会话列表:")
    current_id = current_session.get().session_id
    for i, session in enumerate(sessions, 1):
        marker = "*" if session["id"] == current_id else " "
        created = session.get("created_at", "")[:19].replace("T", " ")
        updated = session.get("updated_at", "")[:19].replace("T", " ")
        print(f"  {marker}{i}. {session['id']}")
        print(f"       创建: {created}")
        print(f"       更新: {updated}")
        print(f"       消息: {session['message_count']} 条")


def _handle_session_switch(session_manager: SessionManager, session_id: str) -> None:
    session = session_manager.load_session(session_id)
    if session:
        current_session.set(session)
        print(f"\n已切换到会话: {session_id}")
    else:
        print(f"\n错误: 无法找到会话 {session_id}")


def _handle_session_new(session_manager: SessionManager) -> None:
    session = session_manager.create_session()
    current_session.set(session)
    print(f"\n已创建新会话: {session.session_id}")


def _handle_session_delete(session_manager: SessionManager, session_id: str) -> None:
    if session_manager.delete_session(session_id):
        print(f"\n已删除会话: {session_id}")
        if current_session.get().session_id == session_id:
            session = session_manager.create_session()
            current_session.set(session)
            print(f"已创建新会话: {session.session_id}")
    else:
        print(f"\n错误: 无法找到会话 {session_id}")


def _handle_session_info(session_manager: SessionManager) -> None:
    print("\n当前会话信息:")
    print(current_session.get().get_summary())


def _handle_session(command: str) -> None:
    session_manager = _get_session_manager()
    if not session_manager:
        print("\n错误: 会话管理器未初始化")
        return

    cmd_parts = command.split(" ", 2)
    if len(cmd_parts) < 2:
        _show_session_help()
        return

    sub_cmd = cmd_parts[1].lower()

    if sub_cmd == "list":
        _handle_session_list(session_manager)
    elif sub_cmd == "switch":
        if len(cmd_parts) < 3:
            print("\n用法: /session switch <会话ID>")
            return
        session_id = cmd_parts[2].strip()
        _handle_session_switch(session_manager, session_id)
    elif sub_cmd == "new":
        _handle_session_new(session_manager)
    elif sub_cmd == "delete":
        if len(cmd_parts) < 3:
            print("\n用法: /session delete <会话ID>")
            return
        session_id = cmd_parts[2].strip()
        _handle_session_delete(session_manager, session_id)
    elif sub_cmd == "info":
        _handle_session_info(session_manager)
    else:
        _show_session_help()


def _get_session_manager() -> SessionManager:
    from code_agent.core.di import container

    return container.session_manager


def register_session_commands(handler) -> None:
    handler.register_command("/session", _handle_session, "会话管理")
