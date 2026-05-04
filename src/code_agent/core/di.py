from dataclasses import dataclass

from opentelemetry import trace

from code_agent.core.config import get_config
from code_agent.core.memory import MemoryManager
from code_agent.core.session_manager import SessionManager


@dataclass
class Container:
    memory_manager: MemoryManager
    session_manager: SessionManager
    tracer: trace.Tracer

    @staticmethod
    def create() -> "Container":
        config = get_config()
        return Container(
            memory_manager=MemoryManager(config),
            session_manager=SessionManager(config.storage.sessions_dir),
            tracer=trace.get_tracer("code_agent"),
        )


container = Container.create()
