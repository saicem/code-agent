#!/usr/bin/env python3
"""
会话上下文管理模块
包含最近的对话内容以及总结信息
"""

import json
from pathlib import Path
from code_agent.config import config
from code_agent.agent import CodeAgent


class SessionContextManager:
    """会话上下文管理类"""

    def __init__(self, platform: str = "ollama", model: str = "llama3"):
        """初始化会话上下文管理器

        Args:
            platform: 模型平台
            model: 模型名称
        """
        self.max_context_length = config.session_context_max_length
        self.max_dialogue_count = config.session_context_max_dialogues
        self.context_file = Path(config.session_context_file)
        self.dialogue_history = self._load_history()
        self.compressed_summary = ""
        self.platform = platform
        self.model = model
        self.agent = None

    def _load_history(self) -> list[dict]:
        """加载对话历史

        Returns:
            对话历史列表
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.compressed_summary = data.get("compressed_summary", "")
                    return data.get("dialogue_history", [])
            except Exception:
                pass
        return []

    def _save_history(self) -> None:
        """保存对话历史"""
        try:
            self.context_file.parent.mkdir(parents=True, exist_ok=True)
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
            # 使用大模型生成摘要
            summary = self._generate_summary_with_llm(old_dialogues)
            if summary:
                self.compressed_summary = summary
            else:
                # 回退到手动摘要
                self.compressed_summary = self._generate_manual_summary(old_dialogues)

        # 只保留最近的对话
        self.dialogue_history = recent_dialogues

    def _generate_summary_with_llm(self, dialogues: list[dict]) -> str:
        """使用大模型生成对话摘要

        Args:
            dialogues: 对话列表

        Returns:
            对话摘要
        """
        try:
            # 初始化模型
            if not self.agent:
                self.agent = CodeAgent.create(platform=self.platform, model=self.model)

            # 构建提示词
            prompt = self._build_summary_prompt(dialogues)

            # 调用模型
            result = self.agent.execute_task(prompt)

            # 提取摘要
            summary = self._extract_summary(result)
            return summary
        except Exception as e:
            print(f"使用大模型生成摘要失败: {e}")
            return ""

    def _build_summary_prompt(self, dialogues: list[dict]) -> str:
        """构建摘要提示词

        Args:
            dialogues: 对话列表

        Returns:
            提示词字符串
        """
        dialogue_texts = []
        for i, dialogue in enumerate(dialogues):
            task = dialogue.get("task", "")
            result = dialogue.get("result", "")
            timestamp = dialogue.get("timestamp", "")
            dialogue_texts.append(f"[{timestamp}] 任务: {task}\n结果: {result}")

        dialogue_content = "\n\n".join(dialogue_texts)

        prompt = f"""请对以下对话历史进行压缩总结，提取关键信息和主要内容：

{dialogue_content}

总结要求：
1. 保持简洁，不超过1000个字符
2. 突出重要的任务和结果
3. 保持逻辑清晰，便于理解
4. 使用中文总结
5. 直接输出总结内容，不要有任何引言或开场白
"""

        return prompt

    def _extract_summary(self, response: str) -> str:
        """提取模型输出的摘要

        Args:
            response: 模型响应

        Returns:
            提取的摘要
        """
        # 简单处理，直接返回响应
        return response.strip()

    def _generate_manual_summary(self, dialogues: list[dict]) -> str:
        """手动生成对话摘要（回退方案）

        Args:
            dialogues: 对话列表

        Returns:
            对话摘要
        """
        summary_parts = []
        summary_parts.append(f"历史对话摘要（共 {len(dialogues)} 条）:")

        # 按时间分组
        for i, dialogue in enumerate(dialogues):
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

        return summary

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

    def get_recent_dialogues(self, count: int = 5) -> list[dict]:
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
