#!/usr/bin/env python3
"""
Code Agent 类
作为核心入口，协调会话管理和推理引擎
"""

import logging
import time

from openai import AsyncOpenAI
from opentelemetry import trace

from code_agent.session import Session
from code_agent.react_engine import ReActEngine
from code_agent.helpers.metrics import (
    record_task_start,
    record_task_completion,
)

tracer = trace.get_tracer("agent")
logger = logging.getLogger(__name__)


class CodeAgent:
    """Code Agent 类（异步版本）"""

    def __init__(self, api_key: str, base_url: str | None = None):
        """初始化 Code Agent

        Args:
            api_key: API 密钥
            base_url: 基础 URL（可选）
        """
        logger.debug(f"初始化 CodeAgent, base_url: {base_url}")
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.react_engine = ReActEngine(self.client)
        logger.info("CodeAgent 初始化完成")

    @tracer.start_as_current_span("execute_task")
    async def execute_task(self, session: Session) -> str:
        """执行任务（异步版本）

        Args:
            session: 会话对象

        Returns:
            执行结果
        """
        task_start_time = time.time()
        logger.debug(f"开始执行任务, 会话ID: {session.session_id}")
        record_task_start()

        try:
            result = await self.react_engine.execute(session)

            task_duration = time.time() - task_start_time
            success = not result.startswith("执行异常") and not result.startswith(
                "执行错误"
            )

            record_task_completion(
                success=success,
                duration=task_duration,
            )

            return result

        except Exception as e:
            task_duration = time.time() - task_start_time
            error_message = str(e)
            logger.error(f"执行任务失败: {error_message}", exc_info=True)
            record_task_completion(success=False, duration=task_duration)
            return f"执行错误: {error_message}"
