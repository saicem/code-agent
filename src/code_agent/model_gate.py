#!/usr/bin/env python3
"""
模型调用门控
处理与模型的交互逻辑
"""

from openai import OpenAI
from code_agent.error_handling import get_env_var


class ModelGate:
    """模型调用门控类"""

    def __init__(self, model: str):
        """初始化模型门控

        Args:
            model: 模型名称
        """
        self.model = model
        self.api_key: str = get_env_var(
            "API_KEY",
            "API key 未设置，请通过环境变量 API_KEY 设置",
        )
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def call_model(self, prompt: str) -> str:
        """调用模型

        Args:
            prompt: 提示词

        Returns:
            模型响应内容
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个代码生成助手，需要根据用户的任务生成正确的代码。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        return content if content is not None else "模型未返回有效响应"

    def _process_response(self, response: str) -> str:
        """处理模型响应

        Args:
            response: 模型响应

        Returns:
            处理后的结果
        """
        # OpenAI API 直接返回内容，不需要额外处理
        return response
