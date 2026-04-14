#!/usr/bin/env python3
"""
文件忽略管理模块
用于读取 .gitignore 文件并提供文件排除功能
"""

import os
import fnmatch


class FileIgnoreManager:
    """文件忽略管理器"""

    def __init__(self, base_dir: str):
        """初始化文件忽略管理器

        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = base_dir
        self.ignore_patterns = self._read_gitignore()

    def _read_gitignore(self) -> list[str]:
        """读取 .gitignore 文件

        Returns:
            忽略规则列表
        """
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            return []

        ignore_patterns = []
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception:
            pass

        return ignore_patterns

    def is_ignored(self, file_path: str) -> bool:
        """检查文件是否被忽略

        Args:
            file_path: 文件路径

        Returns:
            是否被忽略
        """
        relative_path = os.path.relpath(file_path, self.base_dir)

        for pattern in self.ignore_patterns:
            # 处理通配符
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(
                relative_path, pattern.lstrip("/")
            ):
                return True

        return False

    def get_ignored_files(self, directory: str | None = None) -> list[str]:
        """获取被忽略的文件列表

        Args:
            directory: 目录路径，默认为基础目录

        Returns:
            被忽略的文件列表
        """
        if directory is None:
            directory = self.base_dir

        ignored_files = []

        for root, dirs, files in os.walk(directory):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self.is_ignored(os.path.join(root, d))]

            for filename in files:
                file_path = os.path.join(root, filename)
                if self.is_ignored(file_path):
                    ignored_files.append(os.path.relpath(file_path, self.base_dir))

        return ignored_files

    def get_included_files(self, directory: str | None = None) -> list[str]:
        """获取未被忽略的文件列表

        Args:
            directory: 目录路径，默认为基础目录

        Returns:
            未被忽略的文件列表
        """
        if directory is None:
            directory = self.base_dir

        included_files = []

        for root, dirs, files in os.walk(directory):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self.is_ignored(os.path.join(root, d))]

            for filename in files:
                file_path = os.path.join(root, filename)
                if not self.is_ignored(file_path):
                    included_files.append(os.path.relpath(file_path, self.base_dir))

        return included_files
