#!/usr/bin/env python3
"""
工具管理模块
支持异步工具调用、自动发现、动态注册
"""

from code_agent.core.state import tracer

import asyncio
import importlib
import json
import logging
import pkgutil
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Type

from openai.types.chat import (
    ChatCompletionFunctionToolParam,
)
from pydantic import BaseModel, TypeAdapter

from code_agent.core.exceptions import SystemException, ToolError

_logger = logging.getLogger(__name__)

type ToolTag = Literal["code", "plan"]


@dataclass
class ToolInfo:
    """工具信息"""

    name: str
    description: str
    param_type: Type[BaseModel]
    func: Callable
    is_async: bool
    tags: list[ToolTag]
    enabled: bool = True
    timeout: int = 30


class ToolRegistry:
    """工具注册器（单例）"""

    _instance: "ToolRegistry | None" = None
    _tools: dict[str, ToolInfo]
    _tags_map: dict[str, list[str]]

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._tools = {}
            instance._tags_map = {}
            cls._instance = instance
        return cls._instance

    def register(
        self,
        name: str,
        description: str,
        param_type: Type[BaseModel],
        tags: Iterable[ToolTag],
        func: Callable,
        timeout: int = 30,
    ) -> None:
        """注册工具"""
        tool_info = ToolInfo(
            name=name,
            description=description,
            param_type=param_type,
            func=func,
            is_async=asyncio.iscoroutinefunction(func),
            tags=list(tags),
            timeout=timeout,
        )
        self._tools[name] = tool_info
        for tag in tags:
            self._tags_map.setdefault(tag, []).append(name)
        _logger.debug(f"工具注册成功: {name}")

    def unregister(self, name: str) -> bool:
        """注销工具"""
        tool = self._tools.pop(name, None)
        if tool:
            for tag in tool.tags:
                if name in self._tags_map[tag]:
                    self._tags_map[tag].remove(name)
            _logger.info(f"工具注销成功: {name}")
            return True
        return False

    def get_tool(self, name: str) -> ToolInfo | None:
        """获取工具信息"""
        tool = self._tools.get(name)
        return tool if tool and tool.enabled else None

    def get_tools_by_tag(self, tag: ToolTag) -> list[ToolInfo]:
        """获取指定标签的所有工具"""
        tool_names = self._tags_map.get(tag, [])
        return [t for t in (self._tools.get(n) for n in tool_names) if t and t.enabled]

    def enable_tool(self, name: str, enabled: bool) -> None:
        """启用/禁用工具"""
        tool = self._tools.get(name)
        if tool:
            tool.enabled = enabled
            _logger.info(f"工具 {'启用' if enabled else '禁用'}: {name}")

    def get_all_tools(self) -> list[ToolInfo]:
        """获取所有工具"""
        return [t for t in self._tools.values() if t.enabled]


# 全局注册器实例
_tool_registry = ToolRegistry()


def tool[T: Callable](
    name: str,
    description: str,
    param_type: Type[BaseModel],
    tags: Iterable[ToolTag],
    timeout: int = 30,
) -> Callable[[T], T]:
    """工具注册装饰器"""

    def decorator(func: T) -> T:
        _tool_registry.register(
            name=name,
            description=description,
            param_type=param_type,
            tags=tags,
            func=func,
            timeout=timeout,
        )
        return func

    return decorator


def get_tool(tool_name: str) -> ToolInfo | None:
    """获取工具信息"""
    return _tool_registry.get_tool(tool_name)


def tools_for_gen_ai(tag: str) -> list[ChatCompletionFunctionToolParam]:
    """获取指定标签的工具列表（用于 GenAI 调用）"""
    if tag not in ["code", "plan"]:
        raise ValueError(f"无效的标签: {tag}")
    tools = _tool_registry.get_tools_by_tag(tag)  # type: ignore
    if not tools:
        raise SystemException(f"未注册标签 {tag} 的工具")
    return [_build_tool_info(t) for t in tools]


def _build_tool_info(tool_info: ToolInfo) -> ChatCompletionFunctionToolParam:
    """构建工具信息（GenAI 格式）"""
    return {
        "type": "function",
        "function": {
            "name": tool_info.name,
            "description": tool_info.description,
            "parameters": TypeAdapter(tool_info.param_type).json_schema(mode="serialization"),
        },
    }


async def invoke_tool(tool_info: ToolInfo, arguments: str) -> Any:
    """调用工具并返回结果"""
    try:
        params = json.loads(arguments)
    except json.JSONDecodeError as e:
        raise ToolError(f"Invalid tool arguments: {e}") from e

    try:
        validated_params = tool_info.param_type(**params)
    except Exception as e:
        raise ToolError(f"Parameter validation failed: {e}") from e

    if tool_info.is_async:
        return await tool_info.func(validated_params)
    return tool_info.func(validated_params)


@tracer.start_as_current_span("discover_tools")
def discover_tools(package: str = "code_agent.tools") -> None:
    """自动发现并注册所有工具模块"""
    try:
        module = importlib.import_module(package)
        for _, name, is_pkg in pkgutil.iter_modules(module.__path__):
            if not is_pkg and not name.startswith("_"):
                importlib.import_module(f"{package}.{name}")
                _logger.debug(f"自动发现工具模块: {name}")
        _logger.info("工具自动发现完成")
    except Exception as e:
        _logger.error(f"工具自动发现失败: {e}", exc_info=True)
