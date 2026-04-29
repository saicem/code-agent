from code_agent.tools.tool_manager import ToolManager
from code_agent.helpers.file_ignore import FileIgnoreManager
from code_agent.session import SessionManager
from code_agent.commands import CommandHandler
from code_agent.memory import MemoryManager
from code_agent.config import Config

CONFIG = Config()
MEMORY_MANAGER = MemoryManager(CONFIG)
SESSION_MANAGER = SessionManager(CONFIG.sessions_dir)
COMMAND_HANDLER = CommandHandler()
FILE_IGNORE_MANAGER = FileIgnoreManager(CONFIG.base_dir)
