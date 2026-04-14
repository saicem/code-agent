#!/usr/bin/env python3
"""
数据模型模块
定义项目中使用的数据结构
"""

from dataclasses import dataclass


@dataclass
class FileInfo:
    """文件信息数据类"""

    path: str
    size: int
    modified: float
    extension: str
    preview: str


@dataclass
class ProjectContext:
    """项目上下文数据类"""

    file_index: dict[str, FileInfo]
    last_hash: str


@dataclass
class Dialogue:
    """对话数据类"""

    task: str
    result: str
    timestamp: str


@dataclass
class UserPreferences:
    """用户偏好数据类"""

    preferred_language: str | None = None
    preferred_task_type: str | None = None


@dataclass
class UserContext:
    """用户上下文数据类"""

    total_tasks: int = 0
    recent_tasks: list[str] = []
    preferences: UserPreferences | None = None

    def __post_init__(self):
        if self.recent_tasks is None:
            self.recent_tasks = []
        if self.preferences is None:
            self.preferences = UserPreferences()


@dataclass
class CodeBlock:
    """代码块数据类"""

    language: str
    content: str
    file_name: str | None = None


@dataclass
class FileTarget:
    """文件目标数据类"""

    file_name: str
    operation: str
    code: str
    is_temp: bool = False


@dataclass
class ModificationResult:
    """修改结果数据类"""

    success: bool
    message: str
    file_name: str
