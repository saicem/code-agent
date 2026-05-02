"""
Code Agent Metrics 模块
提供各种业务指标的收集和记录
"""

import time
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


# 全局指标对象
_meter = None

# === 指标定义 ===

# 任务相关指标
task_total = None
task_failed_total = None
task_success_total = None
task_duration = None
task_retry_count = None

# 模型调用相关指标
model_call_total = None
model_call_failed_total = None
model_call_duration = None
model_call_token_count = None
model_call_prompt_tokens = None
model_call_completion_tokens = None

# 工具调用相关指标
tool_call_total = None
tool_call_failed_total = None
tool_call_duration = None
tool_call_success_rate = None

# Token 使用相关指标
token_usage_total = None
task_token_count = None

# 会话相关指标
session_total = None
session_active = None
message_total = None

# ReAct 循环相关指标
task_step_count = None
react_cycle_count = None

# 错误相关指标
error_total = None
error_by_type = None


def init_metrics(resource: Resource):
    """初始化 metrics 系统
    
    Args:
        resource: 资源配置
    """
    global _meter
    
    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    
    # 创建全局 meter
    _meter = metrics.get_meter("code_agent")
    
    # 初始化所有指标
    _init_all_metrics()


def _init_all_metrics():
    """初始化所有指标"""
    global task_total, task_failed_total, task_success_total, task_duration, task_retry_count
    global model_call_total, model_call_failed_total, model_call_duration, model_call_token_count
    global model_call_prompt_tokens, model_call_completion_tokens
    global tool_call_total, tool_call_failed_total, tool_call_duration, tool_call_success_rate
    global token_usage_total, task_token_count
    global session_total, session_active, message_total
    global task_step_count, react_cycle_count
    global error_total, error_by_type
    
    meter = metrics.get_meter("code_agent")
    
    # === 任务相关指标 ===
    task_total = meter.create_counter(
        "code_agent.task.total",
        description="任务执行总次数",
        unit="1"
    )
    
    task_failed_total = meter.create_counter(
        "code_agent.task.failed",
        description="任务失败次数",
        unit="1"
    )
    
    task_success_total = meter.create_counter(
        "code_agent.task.success",
        description="任务成功次数",
        unit="1"
    )
    
    task_duration = meter.create_histogram(
        "code_agent.task.duration",
        description="任务执行耗时（秒）",
        unit="s"
    )
    
    task_retry_count = meter.create_histogram(
        "code_agent.task.retries",
        description="任务重试次数",
        unit="1"
    )
    
    # === 模型调用相关指标 ===
    model_call_total = meter.create_counter(
        "code_agent.model.call_total",
        description="模型调用总次数",
        unit="1"
    )
    
    model_call_failed_total = meter.create_counter(
        "code_agent.model.call_failed",
        description="模型调用失败次数",
        unit="1"
    )
    
    model_call_duration = meter.create_histogram(
        "code_agent.model.duration",
        description="模型调用耗时（秒）",
        unit="s"
    )
    
    model_call_token_count = meter.create_histogram(
        "code_agent.model.token_count",
        description="模型调用总token使用量",
        unit="1"
    )
    
    model_call_prompt_tokens = meter.create_histogram(
        "code_agent.model.prompt_tokens",
        description="模型调用提示词token数量",
        unit="1"
    )
    
    model_call_completion_tokens = meter.create_histogram(
        "code_agent.model.completion_tokens",
        description="模型调用补全token数量",
        unit="1"
    )
    
    # === 工具调用相关指标 ===
    tool_call_total = meter.create_counter(
        "code_agent.tool.call_total",
        description="工具调用总次数",
        unit="1"
    )
    
    tool_call_failed_total = meter.create_counter(
        "code_agent.tool.call_failed",
        description="工具调用失败次数",
        unit="1"
    )
    
    tool_call_duration = meter.create_histogram(
        "code_agent.tool.duration",
        description="工具调用耗时（秒）",
        unit="s"
    )
    
    tool_call_success_rate = meter.create_gauge(
        "code_agent.tool.success_rate",
        description="工具调用成功率",
        unit="%"
    )
    
    # === Token 使用相关指标 ===
    token_usage_total = meter.create_counter(
        "code_agent.token.total",
        description="Token使用总量",
        unit="1"
    )
    
    task_token_count = meter.create_histogram(
        "code_agent.task.token_count",
        description="任务Token使用量",
        unit="1"
    )
    
    # === 会话相关指标 ===
    session_total = meter.create_counter(
        "code_agent.session.total",
        description="会话创建总数",
        unit="1"
    )
    
    session_active = meter.create_gauge(
        "code_agent.session.active",
        description="当前活跃会话数",
        unit="1"
    )
    
    message_total = meter.create_counter(
        "code_agent.message.total",
        description="消息总数",
        unit="1"
    )
    
    # === ReAct 循环相关指标 ===
    task_step_count = meter.create_histogram(
        "code_agent.task.step_count",
        description="任务步骤数量",
        unit="1"
    )
    
    react_cycle_count = meter.create_histogram(
        "code_agent.react.cycles",
        description="ReAct循环次数",
        unit="1"
    )
    
    # === 错误相关指标 ===
    error_total = meter.create_counter(
        "code_agent.error.total",
        description="错误总数",
        unit="1"
    )
    
    error_by_type = meter.create_counter(
        "code_agent.error.by_type",
        description="按类型统计的错误数",
        unit="1"
    )


# === 指标记录函数 ===

def record_task_start():
    """记录任务开始"""
    if task_total:
        task_total.add(1, {"status": "started"})


def record_task_completion(success: bool, duration: float, steps: int = 0, retries: int = 0):
    """记录任务完成"""
    if task_duration:
        task_duration.record(duration, {"success": str(success)})
    if task_step_count:
        task_step_count.record(steps)
    if task_retry_count:
        task_retry_count.record(retries)
    
    if success:
        if task_success_total:
            task_success_total.add(1)
    else:
        if task_failed_total:
            task_failed_total.add(1)


def record_model_call(model: str, duration: float, success: bool = True, 
                      total_tokens: int = 0, prompt_tokens: int = 0, completion_tokens: int = 0):
    """记录模型调用"""
    if model_call_total:
        model_call_total.add(1, {"model": model, "success": str(success)})
    if model_call_duration:
        model_call_duration.record(duration, {"model": model})
    
    if success:
        if model_call_token_count:
            model_call_token_count.record(total_tokens, {"model": model})
        if model_call_prompt_tokens:
            model_call_prompt_tokens.record(prompt_tokens, {"model": model})
        if model_call_completion_tokens:
            model_call_completion_tokens.record(completion_tokens, {"model": model})
        if token_usage_total:
            token_usage_total.add(total_tokens)
    else:
        if model_call_failed_total:
            model_call_failed_total.add(1, {"model": model})


def record_tool_call(tool_name: str, duration: float, success: bool = True):
    """记录工具调用"""
    if tool_call_total:
        tool_call_total.add(1, {"tool": tool_name, "success": str(success)})
    if tool_call_duration:
        tool_call_duration.record(duration, {"tool": tool_name})
    
    if not success:
        if tool_call_failed_total:
            tool_call_failed_total.add(1, {"tool": tool_name})


def record_session(count: int):
    """记录会话数量"""
    if session_active:
        session_active.set(count)


def record_session_created():
    """记录会话创建"""
    if session_total:
        session_total.add(1)


def record_message(message_type: str):
    """记录消息"""
    if message_total:
        message_total.add(1, {"type": message_type})


def record_react_cycles(cycles: int):
    """记录ReAct循环次数"""
    if react_cycle_count:
        react_cycle_count.record(cycles)


def record_error(error_type: str):
    """记录错误"""
    if error_total:
        error_total.add(1)
    if error_by_type:
        error_by_type.add(1, {"type": error_type})


def record_task_tokens(tokens: int):
    """记录任务Token使用量"""
    if task_token_count:
        task_token_count.record(tokens)


# 用于记录任务开始时间的字典
_task_timers = {}


def start_task_timer(task_id: str):
    """开始任务计时"""
    _task_timers[task_id] = time.time()


def end_task_timer(task_id: str, success: bool = True, steps: int = 0, retries: int = 0):
    """结束任务计时并记录指标"""
    if task_id in _task_timers:
        duration = time.time() - _task_timers[task_id]
        record_task_completion(success, duration, steps, retries)
        del _task_timers[task_id]
        return duration
    return 0.0
