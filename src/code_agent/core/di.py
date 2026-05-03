from code_agent.core.session_manager import SessionManager
from dataclasses import dataclass
from code_agent.commands import CommandHandler
from opentelemetry import trace
from code_agent.core.config import Config
from code_agent.core.memory import MemoryManager


@dataclass
class Container:
    config: Config
    memory_manager: MemoryManager
    session_manager: SessionManager
    command_handler: CommandHandler
    tracer: trace.Tracer

    @staticmethod
    def create() -> "Container":
        config = Config()
        return Container(
            config=config,
            memory_manager=MemoryManager(config),
            session_manager=SessionManager(config.sessions_dir),
            command_handler=CommandHandler(),
            tracer=trace.get_tracer("code_agent"),
        )


container = Container.create()
