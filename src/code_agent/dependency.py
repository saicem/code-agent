import contextvars
from code_agent.helpers.file_ignore import FileIgnoreManager
from code_agent.session import SessionManager, Session
from code_agent.commands import CommandHandler
from code_agent.memory import MemoryManager
from code_agent.config import Config
from opentelemetry import trace

CONFIG = Config()
MEMORY_MANAGER = MemoryManager(CONFIG)
SESSION_MANAGER = SessionManager(CONFIG.sessions_dir)
COMMAND_HANDLER = CommandHandler()
FILE_IGNORE_MANAGER = FileIgnoreManager(CONFIG.base_dir)
CURRENT_SESSION = contextvars.ContextVar[Session]("current_session")
tracer = trace.get_tracer("code_agent")
