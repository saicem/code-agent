import contextvars

from opentelemetry import trace

from code_agent.agent.session import Session

current_session = contextvars.ContextVar[Session]("current_session")
tracer = trace.get_tracer("code_agent")
