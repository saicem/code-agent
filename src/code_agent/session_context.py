#!/usr/bin/env python3
"""
会话上下文管理模块
"""

import json
import os
from code_agent.config import config


class SessionContextManager:
    """会话上下文管理类"""

    def __init__(self):
        """初始化会话上下文管理器"""
        self.max_context_length = config.session_context_max_length
        self.max_dialogue_count = config.session_context_max_dialogues
        self.context_file = config.session_context_file
        self.dialogue_history = self._load_history()
        self.compressed_summary = ""

    def _load_history(self) -> list[dict[str, str]]:
        """加载对话历史

        Returns:
            对话历史列表
        """
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("dialogue_history", [])
            except Exception:
                return []
        return []

    def _save_history(self) -> None:
        """保存对话历史"""
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "dialogue_history": self.dialogue_history,
                        "compressed_summary": self.compressed_summary,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    def add_dialogue(self, task: str, result: str) -> None:
        """添加对话

        Args:
            task: 任务描述
            result: 执行结果
        """
        self.dialogue_history.append(
            {"task": task, "result": result, "timestamp": self._get_timestamp()}
        )

        # 检查是否需要压缩
        self._check_and_compress()

        self._save_history()

    def _get_timestamp(self) -> str:
        """获取当前时间戳

        Returns:
            时间戳字符串
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _check_and_compress(self) -> None:
        """检查并压缩上下文"""
        current_length = self._calculate_context_length()
        dialogue_count = len(self.dialogue_history)

        if (
            current_length > self.max_context_length
            or dialogue_count > self.max_dialogue_count
        ):
            self._compress_context()

    def _calculate_context_length(self) -> int:
        """计算当前上下文长度

        Returns:
            上下文长度（字符数）
        """
        length = 0
        for dialogue in self.dialogue_history:
            length += len(dialogue.get("task", ""))
            length += len(dialogue.get("result", ""))
        return length

    def _compress_context(self) -> None:
        """压缩上下文"""
        # 保留最近的对话
        recent_dialogues = self.dialogue_history[-3:]

        # 压缩旧的对话为摘要
        old_dialogues = self.dialogue_history[:-3]

        if old_dialogues:
            # 生成摘要
            summary_parts = []
            summary_parts.append(f"历史对话摘要（共 {len(old_dialogues)} 条）:")

            # 按时间分组
            for i, dialogue in enumerate(old_dialogues):
                task = dialogue.get("task", "")
                result = dialogue.get("result", "")

                # 截断过长的内容
                if len(task) > 50:
                    task = task[:50] + "..."
                if len(result) > 100:
                    result = result[:100] + "..."

                summary_parts.append(f"{i + 1}. 任务: {task}")
                summary_parts.append(f"   结果: {result}")

            # 生成摘要并确保不超过 1000 字符
            summary = "\n".join(summary_parts)
            if len(summary) > 1000:
                # 截断摘要
                summary = summary[:997] + "..."

            self.compressed_summary = summary

        # 只保留最近的对话
        self.dialogue_history = recent_dialogues

    def get_context(self, include_summary: bool = True) -> str:
        """获取当前上下文

        Args:
            include_summary: 是否包含压缩摘要

        Returns:
            上下文字符串
        """
        context_parts = []

        # 添加压缩摘要
        if include_summary and self.compressed_summary:
            context_parts.append(self.compressed_summary)
            context_parts.append("\n" + "=" * 50 + "\n")

        # 添加最近的对话
        for i, dialogue in enumerate(self.dialogue_history):
            task = dialogue.get("task", "")
            result = dialogue.get("result", "")
            timestamp = dialogue.get("timestamp", "")

            context_parts.append(f"[{timestamp}] 对话 {i + 1}:")
            context_parts.append(f"任务: {task}")
            context_parts.append(f"结果: {result}")
            context_parts.append("")

        return "\n".join(context_parts)

    def get_recent_dialogues(self, count: int = 5) -> list[dict[str, str]]:
        """获取最近的对话

        Args:
            count: 对话数量

        Returns:
            对话列表
        """
        return self.dialogue_history[-count:]

    def clear_context(self) -> None:
        """清空会话上下文"""
        self.dialogue_history = []
        self.compressed_summary = ""
        self._save_history()

    def get_dialogue_count(self) -> int:
        """获取对话数量

        Returns:
            对话数量
        """
        return len(self.dialogue_history)
