#!/usr/bin/env python3
"""
Ollama 平台的 Agent 实现
"""

import requests
from code_agent.agents.base_agent import BaseAgent


class OllamaAgent(BaseAgent):
    """Ollama 平台的 Agent 实现"""

    def __init__(self, model):
        """初始化 Ollama Agent

        Args:
            model: 模型名称
        """
        super().__init__(model)
        self.base_url = "http://localhost:11434/api"

    def _call_model(self, prompt):
        """调用 Ollama 模型

        Args:
            prompt: 提示词

        Returns:
            模型响应
        """
        url = f"{self.base_url}/generate"
        data = {"model": self.model, "prompt": prompt, "stream": False}

        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()

        return response.json()

    def _process_response(self, response):
        """处理 Ollama 模型响应

        Args:
            response: 模型响应

        Returns:
            处理后的结果
        """
        if "response" in response:
            return response["response"]
        return "模型未返回有效响应"
