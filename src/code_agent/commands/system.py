def _handle_quit(command: str):
    exit()


def _handle_help(command: str):
    from .base import CommandHandler

    handler = CommandHandler()
    print("\n可用指令:")
    sorted_commands = sorted(handler.commands.items())
    for cmd, info in sorted_commands:
        print(f"  {cmd}: {info['description']}")

    print("\n会话管理指令:")
    print("  /session list      - 列出所有会话")
    print("  /session switch <id> - 切换到指定会话")
    print("  /session new       - 创建新会话")
    print("  /session delete <id> - 删除指定会话")
    print("  /session info      - 显示当前会话信息")


def register_system_commands(handler):
    handler.register_command("/quit", _handle_quit, "退出程序")
    handler.register_command("/help", _handle_help, "查看可用指令")
