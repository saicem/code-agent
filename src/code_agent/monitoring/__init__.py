from ._otlp import init_otlp as _init_otlp, get_logger, get_tracer

__all__ = [
    "get_logger",
    "get_tracer",
]


def init() -> None:
    """初始化监控"""
    _init_otlp()
