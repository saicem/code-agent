import contextvars

from code_agent.agent.session import Session

current_session = contextvars.ContextVar[Session]("current_session")
