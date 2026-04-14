#!/usr/bin/env python3
"""
Code Agent 工厂类
"""

from code_agent.agents.ollama_agent import OllamaAgent
from code_agent.agents.bailian_agent import BailianAgent
from code_agent.agents.base_agent import BaseAgent

class CodeAgent:
    """Code Agent 工厂类"""
    
    @staticmethod
    def create(platform, model) -> BaseAgent:
        """创建 Code Agent 实例
        
        Args:
            platform: 平台类型，可选值: "ollama", "bailian"
            model: 模型名称
            
        Returns:
            对应平台的 Agent 实例
        """
        if platform == "ollama":
            return OllamaAgent(model)
        elif platform == "bailian":
            return BailianAgent(model)
        else:
            raise ValueError(f"不支持的平台类型: {platform}")