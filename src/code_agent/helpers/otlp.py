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
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .metrics import init_metrics


def init_otlp():
    """初始化 OTLP 导出器"""
    OpenAIInstrumentor().instrument()

    resource = Resource.create(attributes={SERVICE_NAME: "code-agent"})

    # 先初始化 trace provider（日志需要依赖它）
    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

    # 初始化 logger provider，确保与 trace 关联
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)

    # 配置标准 logging 模块的 handler
    log_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.DEBUG)

    # 初始化 metrics
    init_metrics(resource)

    root_logger.info("OTLP 导出器初始化完成")
