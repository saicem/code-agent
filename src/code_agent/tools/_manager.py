#!/usr/bin/env python3
"""
工具管理模块
支持异步工具调用
"""


import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from openai.types.chat import (
    ChatCompletionFunctionToolParam,
    ChatCompletionToolUnionParam,
)
from pydantic import BaseModel, TypeAdapter

from code_agent import monitoring

_logger = monitoring.get_logger(__name__)


@dataclass
class ToolInfo:
    """工具信息"""

    func: Callable[..., Any]
    is_async: bool


_registered_tools: dict[str, ToolInfo] = {}
_tools_info: dict[str, ChatCompletionToolUnionParam] = {}


def _register_tool[T: Callable](
    name: str, description: str, param_type: type[BaseModel], func: T
) -> None:
    is_async = asyncio.iscoroutinefunction(func)
    _registered_tools[name] = ToolInfo(
        func=func,
        is_async=is_async,
    )
    _tools_info[name] = _build_tool_info(name, description, param_type)


def tool[T: Callable](name: str, description: str, param_type: type[BaseModel]) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        _register_tool(name, description, param_type, func)
        return func

    return decorator


def get_tool(tool_name: str) -> ToolInfo | None:
    """获取工具信息

    Args:
        tool_name: 工具名称

    Returns:
        工具信息或 None
    """
    return _registered_tools.get(tool_name)


def tools_for_gen_ai() -> Iterable[ChatCompletionToolUnionParam]:
    """获取所有注册的工具信息

    Returns:
        工具信息列表
    """
    return _tools_info.values()


def _build_tool_info(
    name: str, description: str, param_type: type[BaseModel]
) -> ChatCompletionFunctionToolParam:
    """构建工具信息

    Returns:
        工具信息列表
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": TypeAdapter(param_type).json_schema(mode="serialization"),
        },
    }

