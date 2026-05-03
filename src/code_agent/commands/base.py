from collections.abc import Callable
from typing import Any

from .session import register_session_commands
from .system import register_system_commands


class CommandHandler:
    def __init__(self):
        self.commands: dict[str, dict[str, Any]] = {}
        self._register_default_commands()

    def _register_default_commands(self):

        register_system_commands(self)
        register_session_commands(self)

    def register_command(self, command: str, handler: Callable[[str], None], description: str):
        self.commands[command] = {"handler": handler, "description": description}

    def unregister_command(self, command: str):
        if command in self.commands:
            del self.commands[command]

    def handle_command(self, command: str) -> bool:
        if not command.startswith("/"):
            return False

        cmd_parts = command.split(" ", 1)
        base_cmd = cmd_parts[0]

        if base_cmd in self.commands:
            handler_info = self.commands[base_cmd]
            handler = handler_info["handler"]
            try:
                handler(command=command)
            except Exception as e:
                print(f"执行指令出错: {e}")
            return True
        else:
            print(f"未知指令: {base_cmd}")
            print("可用指令:")
            for cmd, info in sorted(self.commands.items()):
                print(f"  {cmd}: {info['description']}")
            return True

    def get_available_commands(self) -> dict[str, str]:
        return {cmd: info["description"] for cmd, info in self.commands.items()}
