#!/usr/bin/env python3
"""
百炼平台的 Agent 实现
模型列表 https://help.aliyun.com/zh/model-studio/models
"""

import os
from dashscope import Generation
import dashscope
from code_agent.agents.base_agent import BaseAgent

class BailianAgent(BaseAgent):
    """百炼平台的 Agent 实现"""
    
    def __init__(self, model):
        """初始化百炼 Agent
        
        Args:
            model: 模型名称
        """
        super().__init__(model)
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("百炼 API key 未设置，请通过环境变量 DASHSCOPE_API_KEY 设置")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
    
    def _call_model(self, prompt):
        """调用百炼模型
        
        Args:
            prompt: 提示词
            
        Returns:
            模型响应
        """
        message = [
            {
                "role": "system",
                "content": "你是一个代码生成助手，需要根据用户的任务生成正确的代码。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = Generation.call(
            api_key=self.api_key,
            model=self.model,
            messages=message,
            result_format="json",
            stream=False
        )
               
        return response.json()
    
    def _process_response(self, response):
        """处理百炼模型响应
        
        Args:
            response: 模型响应
            
        Returns:
            处理后的结果
        """
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        return "模型未返回有效响应"