#!/usr/bin/env python3
"""
记忆管理模块
合并用户上下文和项目上下文为"记忆"，存储在 .memo/memory.md
"""

from typing import Any
from code_agent.config import Config

import os
from datetime import datetime


class MemoryManager:
    """记忆管理器
    合并用户上下文和项目上下文，存储在 .memo/memory.md
    """

    def __init__(self, config: Config):
        """初始化记忆管理器

        Args:
            config: 配置对象
        """
        self.base_dir = config.base_dir
        self.memo_dir = os.path.join(self.base_dir, ".memo")
        self.memory_file = os.path.join(self.memo_dir, "memory.md")
        self.sessions_dir = os.path.join(self.memo_dir, "sessions")
        self.last_session_file = os.path.join(self.memo_dir, "last_session.json")

        # 初始化目录
        self._init_dirs()

        # 记忆内容
        self.memory: dict[str, Any] = self._load_memory()

    def _init_dirs(self):
        """初始化目录结构"""
        os.makedirs(self.memo_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _load_memory(self) -> dict[str, Any]:
        """加载记忆文件"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    return self._parse_memory(content)
            except Exception:
                pass
        return {"user_info": {}, "project_info": {}, "history": []}

    def _parse_memory(self, content: str) -> dict[str, Any]:
        """解析记忆文件内容"""
        result: dict[str, Any] = {"user_info": {}, "project_info": {}, "history": []}

        lines = content.split("\n")
        current_section = None

        for line in lines:
            if line.startswith("## 用户信息"):
                current_section = "user_info"
            elif line.startswith("## 项目信息"):
                current_section = "project_info"
            elif line.startswith("## 历史记录"):
                current_section = "history"
            elif line.startswith("## "):
                current_section = None
            elif current_section and line.strip():
                if current_section in ["user_info", "project_info"]:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        section_dict = result[current_section]
                        if isinstance(section_dict, dict):
                            section_dict[key.strip()] = value.strip()
                elif current_section == "history":
                    history_list = result["history"]
                    if isinstance(history_list, list):
                        history_list.append(line.strip())

        return result

    def save_memory(self):
        """保存记忆到文件"""
        content = []
        content.append("# 记忆")
        content.append("")
        content.append("## 用户信息")
        user_info = self.memory.get("user_info", {})
        if isinstance(user_info, dict):
            for key, value in user_info.items():
                content.append(f"{key}: {value}")
        content.append("")
        content.append("## 项目信息")
        project_info = self.memory.get("project_info", {})
        if isinstance(project_info, dict):
            for key, value in project_info.items():
                content.append(f"{key}: {value}")
        content.append("")
        content.append("## 历史记录")
        history = self.memory.get("history", [])
        if isinstance(history, list):
            for item in history:
                content.append(f"- {item}")

        with open(self.memory_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

    def update_user_info(self, key: str, value: str):
        """更新用户信息"""
        user_info = self.memory.get("user_info")
        if isinstance(user_info, dict):
            user_info[key] = value
        self.save_memory()

    def update_project_info(self, key: str, value: str):
        """更新项目信息"""
        project_info = self.memory.get("project_info")
        if isinstance(project_info, dict):
            project_info[key] = value
        self.save_memory()

    def add_history(self, item: str):
        """添加历史记录"""
        history = self.memory.get("history")
        if isinstance(history, list):
            history.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {item}")
            # 保留最近100条记录
            if len(history) > 100:
                history[:] = history[-100:]
        self.save_memory()

    def get_summary(self) -> str:
        """获取记忆摘要"""
        parts = []

        user_info = self.memory.get("user_info")
        if isinstance(user_info, dict) and user_info:
            parts.append("用户信息:")
            for key, value in user_info.items():
                parts.append(f"- {key}: {value}")

        project_info = self.memory.get("project_info")
        if isinstance(project_info, dict) and project_info:
            parts.append("")
            parts.append("项目信息:")
            for key, value in project_info.items():
                parts.append(f"- {key}: {value}")

        history = self.memory.get("history")
        if isinstance(history, list) and history:
            parts.append("")
            parts.append("最近历史:")
            for item in history[-5:]:
                parts.append(f"- {item}")

        return "\n".join(parts)
