#!/usr/bin/env python3
"""
基础 Agent 类
"""

from code_agent.error_handling import ErrorHandler
from code_agent.security import SecurityManager


class BaseAgent:
    """基础 Agent 类"""

    def __init__(self, model):
        """初始化 Agent

        Args:
            model: 模型名称
        """
        self.model = model
        self.error_handler = ErrorHandler()
        self.security_manager = SecurityManager()

    def execute_task(self, task: str) -> str:
        """执行任务

        Args:
            task: 任务描述

        Returns:
            执行结果
        """
        try:
            # 检查任务安全性
            if not self.security_manager.check_task(task):
                return "任务包含不安全内容，无法执行"

            # 直接使用传入的 task 作为提示词（已经在 main.py 中构建了增强提示词）
            prompt = task

            # 调用模型
            response = self._call_model(prompt)

            # 处理响应
            result = self._process_response(response)

            return result

        except Exception as e:
            error_message = self.error_handler.handle_error(e)
            return f"执行错误: {error_message}"

    def _call_model(self, prompt):
        """调用模型

        Args:
            prompt: 提示词

        Returns:
            模型响应
        """
        raise NotImplementedError("子类必须实现 _call_model 方法")

    def _process_response(self, response):
        """处理模型响应

        Args:
            response: 模型响应

        Returns:
            处理后的结果
        """
        raise NotImplementedError("子类必须实现 _process_response 方法")
