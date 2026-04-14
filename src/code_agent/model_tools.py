#!/usr/bin/env python3
"""
大模型工具模块
提供文件内容获取和网络请求功能
"""

import os
import re
import requests
from typing import Dict, Any


class ModelTools:
    """大模型工具类"""

    def __init__(self, base_dir: str):
        """初始化工具类

        Args:
            base_dir: 基础目录，限制文件读取范围
        """
        self.base_dir = base_dir

    def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """获取文件内容

        Args:
            file_path: 文件路径

        Returns:
            包含文件内容的字典
        """
        try:
            # 确保文件路径在基础目录内
            full_path = os.path.abspath(os.path.join(self.base_dir, file_path))
            if not full_path.startswith(self.base_dir):
                return {"success": False, "error": "文件路径超出允许范围"}

            # 检查文件是否存在
            if not os.path.exists(full_path):
                return {"success": False, "error": "文件不存在"}

            # 检查是否是文件
            if not os.path.isfile(full_path):
                return {"success": False, "error": "路径不是文件"}

            # 读取文件内容
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {"success": True, "file_path": file_path, "content": content}
        except Exception as e:
            return {"success": False, "error": f"读取文件失败: {str(e)}"}

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """获取网络请求内容

        Args:
            url: URL 地址

        Returns:
            包含请求结果的字典
        """
        try:
            # 检查是否是有效的 URL
            if not re.match(r"^https?://", url):
                return {"success": False, "error": "无效的 URL 格式"}

            # 发送请求
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 检查是否有 HTTP 错误

            return {
                "success": True,
                "url": url,
                "content": response.text,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"success": False, "error": f"网络请求失败: {str(e)}"}

    def extract_urls(self, text: str) -> list[str]:
        """从文本中提取 URL

        Args:
            text: 文本内容

        Returns:
            URL 列表
        """
        url_pattern = r"https?://[\w\-._~:/?#[\]@!$&\'()*+,;=.]+"
        return re.findall(url_pattern, text)

    def should_fetch_urls(self, text: str) -> bool:
        """判断是否需要进行网络请求

        Args:
            text: 文本内容

        Returns:
            是否需要网络请求
        """
        urls = self.extract_urls(text)
        return len(urls) > 0
