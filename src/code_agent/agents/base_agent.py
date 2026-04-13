#!/usr/bin/env python3
"""
基础 Agent 类
"""

from code_agent.memory import MemoryManager
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
        self.memory_manager = MemoryManager()
        self.error_handler = ErrorHandler()
        self.security_manager = SecurityManager()
    
    def execute_task(self, task):
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
            
            # 构建提示词
            prompt = self._build_prompt(task)
            
            # 调用模型
            response = self._call_model(prompt)
            
            # 处理响应
            result = self._process_response(response)
            
            # 保存到记忆
            self.memory_manager.save_memory(f"任务: {task}\n结果: {result}")
            
            return result
            
        except Exception as e:
            error_message = self.error_handler.handle_error(e)
            return f"执行错误: {error_message}"
    
    def _build_prompt(self, task):
        """构建提示词
        
        Args:
            task: 任务描述
            
        Returns:
            完整提示词
        """
        # 获取记忆
        memory = self.memory_manager.get_memory()
        memory_str = "\n".join(memory[-5:])  # 只使用最近的5条记忆
        
        prompt = f"""
你是一个代码生成助手，需要根据用户的任务生成正确的代码。

最近的记忆:
{memory_str}

任务:
{task}

请生成完整的代码实现，并确保代码正确、安全、高效。
"""
        
        return prompt
    
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
    
    def get_memory(self):
        """获取记忆
        
        Returns:
            记忆列表
        """
        return self.memory_manager.get_memory()