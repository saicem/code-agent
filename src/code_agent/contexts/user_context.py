#!/usr/bin/env python3
"""
用户上下文管理模块
使用 Markdown 文件记录用户信息
"""

import os
from pathlib import Path
from code_agent.config import config


class UserContextManager:
    """用户上下文管理类"""

    def __init__(self):
        """初始化用户上下文管理器"""
        self.context_file = Path(config.user_context_file.replace(".json", ".md"))
        self._ensure_directory()
        self.user_info = self._load_user_info()

    def _ensure_directory(self) -> None:
        """确保目录存在"""
        self.context_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_user_info(self) -> str:
        """加载用户信息

        Returns:
            用户信息内容
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return self._get_default_user_info()

    def _get_default_user_info(self) -> str:
        """获取默认用户信息

        Returns:
            默认用户信息
        """
        return """# 用户信息

## 基本信息
- 用户偏好：待记录
- 编程语言：待记录
- 项目经验：待记录

## 对话历史
暂无对话历史

## 用户偏好
暂无用户偏好
"""

    def _save_user_info(self) -> None:
        """保存用户信息"""
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                f.write(self.user_info)
        except Exception:
            pass

    def update_from_dialogue(self, task: str, result: str) -> None:
        """从对话中更新用户信息

        Args:
            task: 任务描述
            result: 执行结果
        """
        # 检查是否有新的用户信息
        new_info = self._extract_user_info(task, result)
        if new_info:
            self._append_user_info(new_info)
            self._save_user_info()

    def _extract_user_info(self, task: str, result: str) -> str | None:
        """从对话中提取用户信息

        Args:
            task: 任务描述
            result: 执行结果

        Returns:
            提取的用户信息或 None
        """
        # 这里可以添加更复杂的逻辑来提取用户信息
        # 目前只是简单检查是否包含用户偏好相关的信息
        user_info_parts = []

        # 检查编程语言偏好
        languages = ["python", "javascript", "java", "c++", "cpp", "go", "rust"]
        for lang in languages:
            if lang in task.lower() or lang in result.lower():
                user_info_parts.append(f"- 偏好编程语言：{lang}")
                break

        # 检查项目类型偏好
        project_types = ["web", "api", "cli", "desktop", "mobile", "game"]
        for ptype in project_types:
            if ptype in task.lower() or ptype in result.lower():
                user_info_parts.append(f"- 偏好项目类型：{ptype}")
                break

        if user_info_parts:
            return "\n".join(user_info_parts)
        return None

    def _append_user_info(self, new_info: str) -> None:
        """追加用户信息

        Args:
            new_info: 新的用户信息
        """
        # 更新用户偏好部分
        if "## 用户偏好" in self.user_info:
            # 在用户偏好部分添加新信息
            lines = self.user_info.split("\n")
            new_lines = []
            in_preferences = False

            for line in lines:
                new_lines.append(line)
                if line.startswith("## 用户偏好"):
                    in_preferences = True
                elif in_preferences and line.startswith("## "):
                    # 遇到新的章节，插入新信息
                    new_lines.append(new_info)
                    in_preferences = False

            self.user_info = "\n".join(new_lines)
        else:
            # 如果没有用户偏好部分，添加到末尾
            self.user_info += f"\n\n{new_info}"

    def get_context_summary(self) -> str:
        """获取用户上下文摘要

        Returns:
            用户上下文摘要
        """
        return self.user_info

    def clear_context(self) -> None:
        """清空用户上下文"""
        self.user_info = self._get_default_user_info()
        self._save_user_info()
