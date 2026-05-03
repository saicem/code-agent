#!/usr/bin/env python3
"""
会话管理模块
包含 Session 类和 SessionManager 类
"""

import logging
from datetime import datetime
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnionParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

logger = logging.getLogger()


class Session:
    """会话类
    负责管理单个会话的消息，支持 OpenAI 格式的消息结构
    """

    def __init__(self, session_id: str):
        """初始化会话

        Args:
            session_id: 会话ID
        """
        logger.debug(f"创建会话: {session_id}")
        self.session_id = session_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.messages: list[ChatCompletionMessageParam] = []  # 主消息列表（用于发送给模型）
        self.history: list[ChatCompletionMessageParam] = []  # 历史记录（保留所有内容）
        self.system_prompt: str | None = None

    def set_system_prompt(self, content: str):
        """设置系统提示词"""
        self.system_prompt = content

    def add_user_message(self, content: str):
        """添加用户消息"""
        message: ChatCompletionUserMessageParam = {"role": "user", "content": content}
        self.messages.append(message)
        self.history.append(message)
        self.updated_at = datetime.now().isoformat()

    def add_tool_message(self, content: str, tool_call_id: str):
        """添加工具输出消息"""
        message: ChatCompletionToolMessageParam = {
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call_id,
        }
        self.messages.append(message)
        self.history.append(message)
        self.updated_at = datetime.now().isoformat()

    def add_tool_messages(self, tool_messages: list[ChatCompletionToolMessageParam]):
        """添加工具输出消息"""
        self.messages.extend(tool_messages)
        self.history.extend(tool_messages)
        self.updated_at = datetime.now().isoformat()

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[ChatCompletionMessageToolCallUnionParam] | None = None,
    ):
        """添加助手消息"""
        # 在添加助手消息之前，删除 messages 中的所有 tool 消息
        self.messages = [msg for msg in self.messages if msg.get("role") != "tool"]
        message: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": content,
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.messages.append(message)
        self.history.append(message)
        self.updated_at = datetime.now().isoformat()

    def messages_for_model(self) -> list[ChatCompletionMessageParam]:
        """导出消息用于发送给模型

        Returns:
            OpenAI格式的消息列表
        """
        result: list[ChatCompletionMessageParam] = []

        # 添加系统提示词
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})

        # 查找最新的 assistant 输出
        last_assistant_index = -1
        for i in range(len(self.messages) - 1, -1, -1):
            msg = self.messages[i]
            if msg.get("role") == "assistant":
                last_assistant_index = i
                break

        # 导出消息，删除最新 assistant 之前的 tool 输出
        for i, msg in enumerate(self.messages):
            # 如果这是最新的 assistant 之前的 tool 消息，跳过
            if i < last_assistant_index and msg.get("role") == "tool":
                continue

            # 直接添加消息
            result.append(msg)
        return result

    def get_summary(self) -> str:
        """获取会话摘要"""
        summary = f"会话ID: {self.session_id}\n"
        summary += f"创建时间: {self.created_at}\n"
        summary += f"更新时间: {self.updated_at}\n"
        summary += f"消息数量: {len(self.messages)}\n"
        summary += f"历史记录数: {len(self.history)}\n"
        return summary

    def to_dict(self) -> dict[str, Any]:
        """转换为字典用于序列化"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """从字典反序列化"""
        session = cls(data["session_id"])
        session.created_at = data.get("created_at", datetime.now().isoformat())
        session.updated_at = data.get("updated_at", datetime.now().isoformat())
        session.system_prompt = data.get("system_prompt")
        session.messages = data.get("messages", [])
        session.history = data.get("history", [])
        return session
