#!/usr/bin/env python3
"""
基础工具类
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """基础工具类"""

    @abstractmethod
    def run(self, params: str) -> str:
        """运行工具

        Returns:
            工具运行结果
        """
        pass
