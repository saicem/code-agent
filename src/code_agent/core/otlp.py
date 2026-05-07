"""
OpenTelemetry 配置模块
负责初始化和配置 OpenTelemetry 的追踪、日志和指标功能
"""

import json
import logging
import os
from datetime import datetime
from logging import FileHandler, Formatter

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


class JsonFormatter(Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.processName,
            "thread": record.threadName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def get_file_log_handler():
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"code-agent_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    return file_handler


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

    otel_log_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    otel_log_handler.setFormatter(JsonFormatter())
    file_log_handler = get_file_log_handler()

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[otel_log_handler, file_log_handler],
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
