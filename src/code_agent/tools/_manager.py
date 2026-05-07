#!/usr/bin/env python3
"""
工具管理模块
支持异步工具调用
"""

import asyncio
import logging
from dataclasses import dataclass
from functools import cache
from typing import Callable, Iterable, Literal

from openai.types.chat import (
    ChatCompletionFunctionToolParam,
    ChatCompletionToolUnionParam,
)
from pydantic import BaseModel, TypeAdapter

from code_agent.core.exceptions import SystemException

_logger = logging.getLogger(__name__)

type ToolTag = Literal["code", "plan"]


@dataclass
class ToolInfo:
    """工具信息"""

    name: str
    description: str
    param_type: type[BaseModel]
    func: Callable
    is_async: bool


_registered_tools: dict[str, ToolInfo] = {}
_tags_tool_map: dict[str, list[str]] = {}


def _register_tool[T: Callable](
    name: str, description: str, param_type: type[BaseModel], tags: Iterable[ToolTag], func: T
) -> None:
    is_async = asyncio.iscoroutinefunction(func)
    tool_info = ToolInfo(
        name=name,
        description=description,
        param_type=param_type,
        func=func,
        is_async=is_async,
    )
    _registered_tools[name] = tool_info
    for tag in tags:
        _tags_tool_map.setdefault(tag, []).append(name)


def tool[T: Callable](
    name: str, description: str, param_type: type[BaseModel], tags: Iterable[ToolTag]
) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        _register_tool(name, description, param_type, tags, func)
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


@cache
def tools_for_gen_ai(tag: ToolTag) -> Iterable[ChatCompletionToolUnionParam]:
    """获取所有注册的工具信息

    Returns:
        工具信息列表
    """
    tools = _tags_tool_map.get(tag)
    if tools is None:
        raise SystemException(f"未注册标签 {tag} 的工具")
    result = []
    for tool_name in tools:
        tool_info = _registered_tools[tool_name]
        result.append(_build_tool_info(tool_info.name, tool_info.description, tool_info.param_type))
    return result


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
