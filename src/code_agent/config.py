#!/usr/bin/env python3
"""
配置管理模块
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """配置类"""

    # 上下文配置
    session_context_max_length: int = 1000  # 会话上下文最大长度
    session_context_max_dialogues: int = 10  # 会话上下文最大对话数量
    session_context_file: str = ".memo/session_context.json"  # 会话上下文文件路径
    user_context_file: str = ".memo/user_context.md"  # 用户上下文文件路径
    project_context_file: str = ".memo/project_context.json"  # 项目上下文文件路径

    # RAG 配置
    rag_chroma_db_path: str = ".memo/chromadb"  # ChromaDB 存储路径
    rag_similarity_top_k: int = 5  # RAG 检索结果数量

    # 安全配置
    security_check_enabled: bool = True  # 是否启用安全检查

    # 日志配置
    log_file: str = "agent.log"  # 日志文件路径
    log_level: str = "INFO"  # 日志级别

    def __post_init__(self):
        """初始化后确保必要的目录存在"""
        # 确保必要的目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        # 确保 .memo 目录存在
        os.makedirs(".memo", exist_ok=True)
        # 确保 ChromaDB 目录存在
        os.makedirs(self.rag_chroma_db_path, exist_ok=True)


# 创建全局配置实例
config = Config()
