#!/usr/bin/env python3
"""
用户上下文管理模块
"""

import json
import os
from typing import List, Dict, Any


class UserContextManager:
    """用户上下文管理类"""
    
    def __init__(self, context_file=".memo/user_context.json"):
        """初始化用户上下文管理器
        
        Args:
            context_file: 上下文文件路径
        """
        # 确保 .memo 目录存在
        os.makedirs(".memo", exist_ok=True)
        self.context_file = context_file
        self.context = self._load_context()
    
    def _load_context(self) -> Dict[str, Any]:
        """加载用户上下文
        
        Returns:
            用户上下文字典
        """
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_context(self) -> None:
        """保存用户上下文"""
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def update_from_dialogue(self, dialogue_history: List[Dict[str, str]]) -> None:
        """从对话历史中更新用户上下文
        
        Args:
            dialogue_history: 对话历史列表，每个元素包含 task 和 result
        """
        # 提取用户任务
        user_tasks = [item.get("task", "") for item in dialogue_history if item.get("task")]
        
        # 总结用户偏好和模式
        self.context["total_tasks"] = len(user_tasks)
        self.context["recent_tasks"] = user_tasks[-10:]  # 保留最近10个任务
        
        # 分析用户偏好
        if "preferences" not in self.context:
            self.context["preferences"] = {}
        
        # 检测编程语言偏好
        languages = []
        for task in user_tasks:
            if "python" in task.lower():
                languages.append("python")
            elif "javascript" in task.lower():
                languages.append("javascript")
            elif "java" in task.lower():
                languages.append("java")
            elif "c++" in task.lower() or "cpp" in task.lower():
                languages.append("c++")
        
        if languages:
            self.context["preferences"]["preferred_language"] = max(set(languages), key=languages.count)
        
        # 检测任务类型偏好
        task_types = []
        for task in user_tasks:
            if "函数" in task:
                task_types.append("function")
            elif "类" in task:
                task_types.append("class")
            elif "脚本" in task:
                task_types.append("script")
            elif "算法" in task:
                task_types.append("algorithm")
        
        if task_types:
            self.context["preferences"]["preferred_task_type"] = max(set(task_types), key=task_types.count)
        
        self._save_context()
    
    def get_context_summary(self) -> str:
        """获取用户上下文摘要
        
        Returns:
            上下文摘要字符串
        """
        summary_parts = []
        
        if "total_tasks" in self.context:
            summary_parts.append(f"用户已完成 {self.context['total_tasks']} 个任务")
        
        if "preferences" in self.context:
            prefs = self.context["preferences"]
            if "preferred_language" in prefs:
                summary_parts.append(f"偏好编程语言: {prefs['preferred_language']}")
            if "preferred_task_type" in prefs:
                summary_parts.append(f"偏好任务类型: {prefs['preferred_task_type']}")
        
        return "\n".join(summary_parts) if summary_parts else "暂无用户上下文信息"
    
    def get_preferences(self) -> Dict[str, Any]:
        """获取用户偏好
        
        Returns:
            用户偏好字典
        """
        return self.context.get("preferences", {})
    
    def clear_context(self) -> None:
        """清空用户上下文"""
        self.context = {}
        self._save_context()
