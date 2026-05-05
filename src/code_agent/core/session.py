#!/usr/bin/env python3
"""
会话管理模块
包含 Session 类和 SessionManager 类
"""

from dataclasses import dataclass, field
from datetime import datetime

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnionParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from code_agent.monitoring import get_logger, get_tracer

_logger = get_logger(__name__)
_tracer = get_tracer(__name__)


@dataclass
class SessionData:
    """会话数据模型
    用于会话的序列化和反序列化
    """

    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    parent_session_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_token: int = 0
    system_prompt: str = ""
    messages: list[ChatCompletionMessageParam] = field(default_factory=list)
    history: list[ChatCompletionMessageParam] = field(default_factory=list)


class Session:
    """会话类
    负责管理单个会话的消息，支持 OpenAI 格式的消息结构
    """

    def __init__(self, data: SessionData | None = None):
        self.data = SessionData() if data is None else data

    def set_system_prompt(self, content: str):
        """设置系统提示词"""
        self.system_prompt = content

    def add_user_message(self, content: str):
        """添加用户消息"""
        message: ChatCompletionUserMessageParam = {"role": "user", "content": content}
        self.data.messages.append(message)
        self.data.history.append(message)
        self.updated_at = datetime.now().isoformat()

    def add_tool_message(self, content: str, tool_call_id: str):
        """添加工具输出消息"""
        message: ChatCompletionToolMessageParam = {
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call_id,
        }
        self.data.messages.append(message)
        self.data.history.append(message)
        self.updated_at = datetime.now().isoformat()

    def add_tool_messages(self, tool_messages: list[ChatCompletionToolMessageParam]):
        """添加工具输出消息"""
        self.data.messages.extend(tool_messages)
        self.data.history.extend(tool_messages)
        self.updated_at = datetime.now().isoformat()

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[ChatCompletionMessageToolCallUnionParam] | None = None,
    ):
        message: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": content,
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.data.messages.append(message)
        self.data.history.append(message)
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
        for i in range(len(self.data.messages) - 1, -1, -1):
            msg = self.data.messages[i]
            if msg.get("role") == "assistant":
                last_assistant_index = i
                break

        # 导出消息，删除最新 assistant 之前的 tool 输出
        for i, msg in enumerate(self.data.messages):
            # 如果这是最新的 assistant 之前的 tool 消息，跳过
            if i < last_assistant_index and msg.get("role") == "tool":
                continue

            # 直接添加消息
            result.append(msg)
        return result

    @classmethod
    def from_dict(cls, **kwargs) -> "Session":
        """从字典反序列化"""
        return cls(SessionData(**kwargs))

    def clear_message(self) -> None:
        self.data.messages = []

    def _clean_message(self) -> None:
        self.data.messages = [msg for msg in self.data.messages if msg.get("role") != "tool"]
