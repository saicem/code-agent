from typing import Any, Callable

from code_agent.commands.session import register_session_commands
from code_agent.commands.system import register_system_commands


class CommandHandler:
    def __init__(self):
        self._commands: dict[str, dict[str, Any]] = {}
        register_system_commands(self)
        register_session_commands(self)
        self.register_command("help", self._handle_help(), description="查看可用指令")

    def register_command(self, command: str, handler: Callable[[str], None], description: str):
        self._commands[command] = {"handler": handler, "description": description}

    def unregister_command(self, command: str):
        if command in self._commands:
            del self._commands[command]

    def handle_command(self, command: str) -> bool:
        if not command.startswith("/"):
            return False

        cmd_parts = command.split(" ", 1)
        base_cmd = cmd_parts[0]

        if base_cmd in self._commands:
            handler_info = self._commands[base_cmd]
            handler = handler_info["handler"]
            try:
                handler(command=command)
            except Exception as e:
                print(f"执行指令出错: {e}")
            return True
        else:
            print(f"未知指令: {base_cmd}")
            print("可用指令:")
            for cmd, info in sorted(self._commands.items()):
                print(f"  {cmd}: {info['description']}")
            return True

    def get_available_commands(self) -> dict[str, str]:
        return {cmd: info["description"] for cmd, info in self._commands.items()}

    def _handle_help(self):
        def help_command(_command: str):
            sorted_commands = sorted(self._commands.items())
            for cmd, info in sorted_commands:
                print(f"  {cmd}: {info['description']}")
            print("\n可用指令:")
            print("\n会话管理指令:")
            print("  /session list      - 列出所有会话")
            print("  /session switch <id> - 切换到指定会话")
            print("  /session new       - 创建新会话")
            print("  /session delete <id> - 删除指定会话")
            print("  /session info      - 显示当前会话信息")

        return help_command


_command_handler = CommandHandler()


def handle_command(command: str):
    _command_handler.handle_command(command)
