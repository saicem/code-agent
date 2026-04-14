#!/usr/bin/env python3
"""
断言工具类
用于处理类型推断模糊的情况
"""

from typing import TypeVar, Type, Any

T = TypeVar("T")


class AssertTool:
    """断言工具类"""

    @staticmethod
    def assert_type(value: Any, expected_type: Type[T]) -> T:
        """断言值的类型

        Args:
            value: 要检查的值
            expected_type: 期望的类型

        Returns:
            类型检查通过后的值

        Raises:
            TypeError: 如果值的类型不符合期望
        """
        if not isinstance(value, expected_type):
            print(
                f"断言失败: 期望类型 {expected_type.__name__}，实际类型 {type(value).__name__}，值为 {value}"
            )
            raise TypeError(
                f"期望类型 {expected_type.__name__}，实际类型 {type(value).__name__}"
            )
        return value

    @staticmethod
    def assert_not_none(value: Any) -> Any:
        """断言值不为 None

        Args:
            value: 要检查的值

        Returns:
            非 None 的值

        Raises:
            ValueError: 如果值为 None
        """
        if value is None:
            print("断言失败: 值不能为 None")
            raise ValueError("值不能为 None")
        return value

    @staticmethod
    def assert_instance(value: Any, expected_types: tuple[Type[Any], ...]) -> Any:
        """断言值是指定类型之一

        Args:
            value: 要检查的值
            expected_types: 期望的类型元组

        Returns:
            类型检查通过后的值

        Raises:
            TypeError: 如果值的类型不符合任何期望类型
        """
        if not isinstance(value, expected_types):
            expected_names = [t.__name__ for t in expected_types]
            print(
                f"断言失败: 期望类型之一 {expected_names}，实际类型 {type(value).__name__}，值为 {value}"
            )
            raise TypeError(
                f"期望类型之一 {expected_names}，实际类型 {type(value).__name__}"
            )
        return value
