#!/usr/bin/env python3
"""
文件忽略管理模块
用于读取 .gitignore 文件并提供文件排除功能
"""

from pathspec import GitIgnoreSpec


def get_pathspec_from_gitignore(gitignore: str) -> GitIgnoreSpec:
    with open(gitignore, "r", encoding="utf-8") as f:
        return GitIgnoreSpec.from_lines(f.readlines())
