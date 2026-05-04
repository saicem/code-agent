from code_agent.monitoring._otlp import get_logger, get_tracer
from code_agent.monitoring._otlp import init_otlp as _init_otlp

__all__ = [
    "get_logger",
    "get_tracer",
]


def init() -> None:
    """初始化监控"""
    _init_otlp()
