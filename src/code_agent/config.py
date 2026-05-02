#!/usr/bin/env python3
"""
配置管理模块
"""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from os.path import join
from os import makedirs


class Config(BaseSettings):
    """配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        cli_parse_args=True,
    )

    # OpenAI 配置
    api_key: str = Field(default="", description="OpenAI API 密钥")
    base_url: str | None = Field(default=None, description="OpenAI API 基础 URL")
    model: str = Field(default="gpt-4o-mini", description="模型名称")

    # 基础配置
    base_dir: str = Field(default=".", description="基础目录")
    storage_dir: str = Field(
        default_factory=lambda data: join(data["base_dir"], ".memo"),
        description="存储目录",
    )

    # 上下文配置
    session_context_max_length: int = Field(
        default=1000, description="会话上下文最大长度"
    )
    session_context_max_dialogues: int = Field(
        default=10, description="会话上下文最大对话数量"
    )
    session_context_file: str = Field(
        default_factory=lambda data: join(data["storage_dir"], "session_context.json"),
        description="会话上下文文件路径",
    )
    memory_file: str = Field(
        default_factory=lambda data: join(data["storage_dir"], "memory.md"),
        description="记忆文件路径",
    )
    sessions_dir: str = Field(
        default_factory=lambda data: join(data["storage_dir"], "sessions"),
        description="会话目录",
    )

    # 安全配置
    security_check_enabled: bool = Field(default=True, description="是否启用安全检查")

    # 日志配置
    log_file: str = Field(
        default_factory=lambda data: join(data["base_dir"], "agent.log"),
        description="日志文件路径",
    )
    log_level: str = Field(default="INFO", description="日志级别")
    otlp_enabled: bool = Field(default=False, description="是否启用 OTLP 导出器")

    # 循环配置
    react_max_cycles: int = Field(default=20, description="ReAct 最大循环次数")

    @model_validator(mode="after")
    def _post_init(self) -> "Config":
        self._ensure_directories()
        return self

    def _ensure_directories(self):
        """确保必要的目录存在"""
        makedirs(self.storage_dir, exist_ok=True)
        makedirs(self.sessions_dir, exist_ok=True)
