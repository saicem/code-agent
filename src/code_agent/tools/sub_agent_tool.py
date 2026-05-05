#!/usr/bin/env python3
"""
子Agent工具模块
用于分发独立任务，保持父Agent上下文清晰
"""

import json
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from code_agent import monitoring
from code_agent.agent.gate import ModelGate
from code_agent.core.config import get_config
from code_agent.core.session import Session
from code_agent.tools._manager import tool

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)


class SubAgentTaskParams(BaseModel):
    """子Agent任务参数"""

    task: str = Field(description="需要子Agent完成的独立任务描述")
    system_prompt: Optional[str] = Field(
        default=None, description="子Agent使用的系统提示词，可选，默认使用标准提示词"
    )
    max_cycles: Optional[int] = Field(default=10, description="子Agent最大推理循环次数，默认10次")


@tool(
    name="delegate_to_sub_agent",
    description="将独立的子任务委托给子Agent执行，并返回结果摘要。适用于代码分析、文档生成、复杂问题分解等需要独立推理的场景，可保持主Agent上下文整洁。",
    param_type=SubAgentTaskParams,
)
async def run_sub_agent_task(params: str) -> str:
    """
    执行子Agent任务

    Args:
        params: JSON格式的参数，包含task、system_prompt、max_cycles

    Returns:
        JSON格式的执行结果
    """
    # 延迟导入，避免循环依赖
    from code_agent.agent.engine import execute_reasoning_acting

    try:
        # 解析参数
        params_dict = json.loads(params)
        task = params_dict.get("task", "")
        system_prompt = params_dict.get("system_prompt", None)
        max_cycles = params_dict.get("max_cycles", 10)

        if not task:
            return json.dumps(
                {"success": False, "message": "任务描述不能为空", "data": None},
                ensure_ascii=False,
            )

        _logger.info(f"子Agent任务开始: {task[:50]}...")

        # 创建独立的子会话（使用随机ID）
        sub_session_id = f"sub_agent_{uuid.uuid4().hex[:8]}"
        sub_session = Session(sub_session_id)

        # 设置自定义系统提示词或使用默认提示词
        if system_prompt:
            sub_session.set_system_prompt(system_prompt)
        else:
            # 默认子Agent提示词
            default_prompt = """
你是一个专业的任务分析助手。请独立完成以下任务，并返回详细的分析结果或解决方案。

任务要求：
1. 仔细分析问题
2. 如果需要，可以调用工具获取信息
3. 返回清晰、结构化的结果
4. 结果将被用于帮助父Agent完成更大的任务

请用中文回答。
"""
            sub_session.set_system_prompt(default_prompt.strip())

        # 添加用户任务
        sub_session.add_user_message(task)

        # 获取配置
        config = get_config()

        # 创建子Agent的React配置
        react_config = config.react.model_copy()
        react_config.max_cycles = max_cycles

        # 创建ModelGate（复用父Agent的客户端配置）
        model_gate = ModelGate(config.gate)

        # 执行子任务（使用独立的推理循环）
        await execute_reasoning_acting(model_gate, sub_session, react_config)

        # 获取子任务的结果摘要
        messages = list(sub_session.messages)
        result_summary = "子任务执行完成，但未生成具体结果"

        # 提取助手的最终回复
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if content:
                    result_summary = str(content)
                    break

        # 截断过长的摘要
        summary_preview = result_summary[:50] if len(result_summary) > 50 else result_summary
        _logger.info(f"子Agent任务完成: {summary_preview}...")

        return json.dumps(
            {
                "success": True,
                "message": "子任务执行成功",
                "data": {
                    "summary": result_summary,
                    "total_messages": len(messages),
                    "task": task,
                },
            },
            ensure_ascii=False,
        )

    except json.JSONDecodeError as e:
        _logger.error(f"参数解析失败: {e}")
        return json.dumps(
            {"success": False, "message": f"参数解析失败: {e!s}", "data": None},
            ensure_ascii=False,
        )
    except Exception as e:
        _logger.error(f"子Agent任务执行失败: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"子任务执行失败: {e!s}", "data": None},
            ensure_ascii=False,
        )
