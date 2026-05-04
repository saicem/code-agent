def _handle_quit(command: str):
    exit()


def register_system_commands(handler):
    handler.register_command("/quit", _handle_quit, "退出程序")
