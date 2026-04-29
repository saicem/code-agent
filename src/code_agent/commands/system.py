

def _handle_quit(command: str):
    exit()
    pass


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


def _handle_about(command: str):
    args = global_context.args
    if args:
        print("\nCode Agent 信息:")
        print("版本: 0.1.0")
        print(f"平台: {args.platform}")
        print(f"模型: {args.model}")
        print(f"项目目录: {args.project_dir}")
        print(f"应用修改: {'开启' if args.apply_changes else '关闭'}")
        if args.output:
            print(f"输出文件: {args.output}")


def register_system_commands(handler):
    handler.register_command("/quit", _handle_quit, "退出程序")
    handler.register_command("/about", _handle_about, "显示当前信息")
    handler.register_command("/help", _handle_help, "查看可用指令")
