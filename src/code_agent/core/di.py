from code_agent.core.session_manager import SessionManager
from dataclasses import dataclass
from code_agent.commands import CommandHandler
from opentelemetry import trace
from code_agent.core.config import get_config
from code_agent.core.memory import MemoryManager


@dataclass
class Container:
    memory_manager: MemoryManager
    session_manager: SessionManager
    command_handler: CommandHandler
    tracer: trace.Tracer

    @staticmethod
    def create() -> "Container":
        config = get_config()
        return Container(
            memory_manager=MemoryManager(config),
            session_manager=SessionManager(config.storage.sessions_dir),
            command_handler=CommandHandler(),
            tracer=trace.get_tracer("code_agent"),
        )


container = Container.create()
