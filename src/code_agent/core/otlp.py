"""
OpenTelemetry 配置模块
负责初始化和配置 OpenTelemetry 的追踪、日志和指标功能
"""

import logging

from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_otlp():
    """初始化 OTLP 导出器"""
    OpenAIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    resource = Resource.create(attributes={SERVICE_NAME: "code-agent"})

    # 先初始化 trace provider（日志需要依赖它）
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(trace_provider)

    # 初始化 logger provider，确保与 trace 关联
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    _logs.set_logger_provider(logger_provider)

    # 配置标准 logging 模块的 handler
    log_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[log_handler],
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
