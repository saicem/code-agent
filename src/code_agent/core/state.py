import contextvars

from opentelemetry import trace

from code_agent.agent.session import Session


class SessionContext:
    """会话上下文管理器
    提供类型安全的会话状态管理
    """

    _var = contextvars.ContextVar[Session]("current_session")

    @classmethod
    def get(cls) -> Session:
        """获取当前会话
        Raises:
            RuntimeError: 如果没有活跃会话
        """
        session = cls._var.get(None)
        if session is None:
            raise RuntimeError("No active session. Call set() first.")
        return session

    @classmethod
    def set(cls, session: Session) -> contextvars.Token:
        """设置当前会话
        Returns:
            Token for resetting
        """
        return cls._var.set(session)

    @classmethod
    def reset(cls, token: contextvars.Token) -> None:
        """重置会话到之前的状态"""
        cls._var.reset(token)


current_session = SessionContext()
tracer = trace.get_tracer("code_agent")
