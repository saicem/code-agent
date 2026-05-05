#!/usr/bin/env python3
"""
文件忽略管理模块
用于读取 .gitignore 文件并提供文件排除功能
"""

from pathspec import GitIgnoreSpec

# 定义默认的忽略 spec
DEFAULT_IGNORE_SPEC = GitIgnoreSpec.from_lines(
    [
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "pycache",
        "pycache__",
        "__pycache__",
        ".memo",
        ".ruff_cache",
        "dist",
    ]
)


def get_pathspec_from_gitignore(gitignore: str) -> GitIgnoreSpec | None:
    try:
        with open(gitignore, "r", encoding="utf-8") as f:
            return GitIgnoreSpec.from_lines(f.readlines())
    except FileNotFoundError:
        return None
