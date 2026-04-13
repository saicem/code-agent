#!/usr/bin/env python3
"""
记忆管理模块
"""

import json
import os

class MemoryManager:
    """记忆管理类"""
    
    def __init__(self, memory_file=".memo/memory.json"):
        """初始化记忆管理器
        
        Args:
            memory_file: 记忆文件路径
        """
        # 确保 .memo 目录存在
        os.makedirs(".memo", exist_ok=True)
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self):
        """加载记忆
        
        Returns:
            记忆列表
        """
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def save_memory(self, content):
        """保存记忆
        
        Args:
            content: 记忆内容
        """
        self.memory.append(content)
        # 只保留最近的100条记忆
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
        
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_memory(self):
        """获取记忆
        
        Returns:
            记忆列表
        """
        return self.memory
    
    def clear_memory(self):
        """清空记忆"""
        self.memory = []
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f)
        except Exception:
            pass
