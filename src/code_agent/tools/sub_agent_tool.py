#!/usr/bin/env python3
"""
子Agent工具模块
用于分发独立任务，保持父Agent上下文清晰
"""

import json
import logging

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel, Field

from code_agent.agent.prompt import CODE_SYSTEM
from code_agent.agent.session import Session
from code_agent.agent.session_manager import SessionManager
from code_agent.core.container import Container
from code_agent.core.exceptions import ToolException
from code_agent.core.state import current_session
from code_agent.tools._manager import tool
from code_agent.utils import print_tool_output
from code_agent.utils.tool_util import build_tool_response

_logger = logging.getLogger(__name__)


class SubAgentTaskParams(BaseModel):
    """子Agent任务参数"""

    task: str = Field(description="需要子Agent完成的独立任务描述")


@tool(
    name="delegate_to_sub_agent",
    description="将独立的子任务委托给子Agent执行，并返回结果摘要。适用于代码分析、文档生成、复杂问题分解等需要独立推理的场景，可保持主Agent上下文整洁。",
    param_type=SubAgentTaskParams,
    tags=["plan"],
)
@inject
async def run_sub_agent_task(
    params: str, session_manager: SessionManager = Provide[Container.session_manager]
) -> str:
    # 延迟导入，避免循环依赖
    from code_agent.agent.engine import reasoning_acting

    # 解析参数
    validated_params = SubAgentTaskParams.model_validate_json(params)

    if not validated_params.task:
        return json.dumps(
            {"success": False, "message": "任务描述不能为空", "data": None},
            ensure_ascii=False,
        )

    print_tool_output(f"委托子任务: {validated_params.task}", "delegate_to_sub_agent")
    sub_session = Session()
    sub_session.set_system_prompt(CODE_SYSTEM)
    sub_session.add_user_message(validated_params.task)
    sub_session.data.parent_session_id = current_session.get().data.session_id

    # 保存当前会话并设置子会话
    token = current_session.set(sub_session)
    try:
        await reasoning_acting(sub_session, "code")
    finally:
        # 恢复原来的会话
        current_session.reset(token)

    # 保存子会话
    session_manager.save_session(sub_session)

    if not sub_session.data.messages:
        _logger.error("子Agent没有返回任何消息")
        raise ToolException("子Agent没有返回任何消息")

    last_message = sub_session.data.messages[-1]
    if isinstance(last_message, dict) and last_message.get("role") == "assistant":
        summary = last_message.get("content", "")
    else:
        _logger.error(f"子Agent返回的不是文本消息 {last_message}")
        raise ToolException("子Agent返回的不是文本消息")
    return build_tool_response(
        True,
        "子任务执行成功",
        {
            "summary": summary,
            "total_messages": len(sub_session.data.messages),
        },
    )
