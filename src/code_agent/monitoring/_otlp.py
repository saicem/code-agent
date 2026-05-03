"""
OpenTelemetry 配置模块
负责初始化和配置 OpenTelemetry 的追踪、日志和指标功能
"""

import logging
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from opentelemetry import trace
from opentelemetry import _logs
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_resource: Resource | None = None
_trace_provider: trace.TracerProvider | None = None
_logger_provider: LoggerProvider | None = None
_log_handler: LoggingHandler | None = None


def init_otlp():
    global _resource, _trace_provider, _logger_provider, _log_handler
    """初始化 OTLP 导出器"""
    OpenAIInstrumentor().instrument()

    _resource = Resource.create(attributes={SERVICE_NAME: "code-agent"})

    # 先初始化 trace provider（日志需要依赖它）
    _trace_provider = TracerProvider(resource=_resource)
    _trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(_trace_provider)

    # 初始化 logger provider，确保与 trace 关联
    _logger_provider = LoggerProvider(resource=_resource)
    _logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter())
    )
    _logs.set_logger_provider(_logger_provider)

    # 配置标准 logging 模块的 handler
    _log_handler = LoggingHandler(
        level=logging.NOTSET, logger_provider=_logger_provider
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(_log_handler)
    root_logger.setLevel(logging.DEBUG)
    root_logger.info("OTLP 导出器初始化完成")


def get_tracer(name: str, provider: trace.TracerProvider | None = None) -> trace.Tracer:
    return trace.get_tracer(name, tracer_provider=provider)


def get_logger(
    name: str, level: int = logging.DEBUG, handler: logging.Handler | None = None
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if handler:
        logger.addHandler(handler)
    elif _log_handler:
        logger.addHandler(_log_handler)
    return logger
