#!/usr/bin/env python3
"""
错误处理模块
"""

import os
import traceback
import logging
import requests
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="agent.log",
    encoding="utf-8",
)


class ErrorHandler:
    """错误处理器"""

    def handle_error(self, error):
        """处理错误

        Args:
            error: 错误对象

        Returns:
            错误消息
        """
        # 记录错误日志
        error_message = str(error)
        error_traceback = traceback.format_exc()

        logging.error(f"错误: {error_message}")
        logging.error(f"堆栈跟踪: {error_traceback}")

        # 根据错误类型返回不同的错误消息
        if isinstance(error, requests.RequestException):
            return "模型调用失败，请检查 ollama 服务是否运行"
        elif isinstance(error, json.JSONDecodeError):
            return "JSON 解析错误"
        elif isinstance(error, FileNotFoundError):
            return "文件未找到"
        else:
            return error_message

    def validate_input(self, input_data):
        """验证输入

        Args:
            input_data: 输入数据

        Returns:
            (是否有效, 错误消息)
        """
        if not input_data:
            return False, "输入不能为空"

        if len(input_data) > 1000:
            return False, "输入长度不能超过 1000 字符"

        return True, ""


def get_env_var(var_name: str, error_message: str) -> str:
    """从环境变量获取值，如果获取不到则报错

    Args:
        var_name: 环境变量名称
        error_message: 自定义错误消息

    Returns:
        环境变量的值

    Raises:
        ValueError: 环境变量未设置时
    """
    value = os.getenv(var_name)
    if not value:
        if error_message:
            raise ValueError(error_message)
        else:
            raise ValueError(f"环境变量 {var_name} 未设置")
    return value
