#!/usr/bin/env python3
"""
基础工具类
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """基础工具类"""

    @abstractmethod
    def name(self) -> str:
        """获取工具名称

        Returns:
            工具名称
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """获取工具描述

        Returns:
            工具描述
        """
        pass

    @abstractmethod
    def parameters(self) -> dict[str, object]:
        """获取工具参数

        Returns:
            工具参数字典
        """
        pass

    @abstractmethod
    def run(self, params: str) -> str:
        """运行工具

        Returns:
            工具运行结果
        """
        pass
