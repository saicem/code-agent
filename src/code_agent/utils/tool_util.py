#!/usr/bin/env python3
"""
工具函数模块
提供参数校验和路径构建等通用功能
"""

import json
import os
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from code_agent.core.exceptions import ToolError


def validate_params[T: BaseModel](params: str, param_type: Type[T]) -> T:
    """
    校验参数并返回解析结果

    Args:
        params: JSON 格式的参数字符串
        param_type: Pydantic 模型类

    Returns:
        解析后的参数对象

    Raises:
        ToolException: 如果参数验证失败或 JSON 解析失败
    """
    try:
        validated_params = param_type.model_validate_json(params)
        return validated_params
    except ValidationError as e:
        raise ToolError(f"参数验证失败: {e!s}") from e
    except json.JSONDecodeError as e:
        raise ToolError(f"JSON 解析失败: {e!s}") from e


def build_full_path(file_path: str, base_dir: str | None = None) -> str:
    """
    构建完整的文件路径

    Args:
        file_path: 相对文件路径
        base_dir: 基础目录，默认为当前工作目录

    Returns:
        完整路径

    Raises:
        ToolException: 如果路径超出允许范围
    """
    if base_dir is None:
        base_dir = os.path.abspath(os.getcwd())

    full_path = os.path.join(base_dir, file_path)
    full_path = os.path.abspath(full_path)

    # 确保路径在基础目录内
    if not full_path.startswith(base_dir):
        raise ToolError("文件路径超出允许范围")

    return full_path


def build_tool_response(success: bool, message: str, data: Any = None) -> str:
    """
    构建统一格式的工具响应 JSON

    Args:
        success: 是否成功
        message: 消息
        data: 其他附加数据

    Returns:
        JSON 格式的工具响应字符串
    """
    result = {
        "success": success,
        "message": message,
        "data": data,
    }
    return json.dumps(result, ensure_ascii=False)
