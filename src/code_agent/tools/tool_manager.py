#!/usr/bin/env python3
"""
工具管理类
"""

from typing import Dict, Type, List, Any
from code_agent.tools.base_tool import BaseTool


class ToolManager:
    """工具管理类"""

    # 存储所有注册的工具类
    _registered_tools: Dict[str, Type[BaseTool]] = {}

    @classmethod
    def register_tool(cls, tool_class: Type[BaseTool]) -> Type[BaseTool]:
        """注册工具装饰器

        Args:
            tool_class: 工具类

        Returns:
            工具类
        """
        # 获取工具名称
        tool_name = tool_class.name(tool_class())
        cls._registered_tools[tool_name] = tool_class
        return tool_class

    @classmethod
    def get_tool(cls, tool_name: str) -> Type[BaseTool] | None:
        """获取工具类

        Args:
            tool_name: 工具名称

        Returns:
            工具类或 None
        """
        return cls._registered_tools.get(tool_name)

    @classmethod
    def get_all_tools(cls) -> Dict[str, Type[BaseTool]]:
        """获取所有注册的工具类

        Returns:
            工具类字典
        """
        return cls._registered_tools

    @classmethod
    def create_tool_instance(cls, tool_name: str) -> BaseTool | None:
        """创建工具实例

        Args:
            tool_name: 工具名称
            **kwargs: 工具初始化参数

        Returns:
            工具实例或 None
        """
        tool_class = cls.get_tool(tool_name)
        if tool_class:
            try:
                return tool_class()
            except Exception as e:
                print(f"创建工具 {tool_name} 实例失败: {e}")
        return None
