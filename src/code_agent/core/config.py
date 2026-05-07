#!/usr/bin/env python3
"""
配置管理模块
将配置项分组到不同的配置类中，便于不同模块精确传入所需配置
"""

from os import makedirs
from os.path import abspath, join
from typing import Self

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GateConfig(BaseModel):
    """OpenAI API 配置"""

    api_key: str = Field(default=..., description="OpenAI API 密钥")
    base_url: str | None = Field(default=None, description="OpenAI API 基础 URL")
    model: str = Field(default="gpt-4o-mini", description="模型名称")


class StorageConfig(BaseModel):
    """存储相关配置"""

    base_dir: str = Field(default=".", description="基础目录")
    storage_dir: str = Field(default="", description="存储目录")
    sessions_dir: str = Field(default="", description="会话目录")
    auto_memory: str = Field(default="", description="自动记忆文件路径")
    file_update: str = Field(default="", description="文件更新记录文件路径")

    @model_validator(mode="after")
    def _post_init(self) -> Self:
        """初始化后处理：填充依赖路径并确保目录存在"""
        if not self.storage_dir:
            self.storage_dir = abspath(join(self.base_dir, ".memo"))

        if not self.sessions_dir:
            self.sessions_dir = join(self.storage_dir, "sessions")

        if not self.auto_memory:
            self.auto_memory = join(self.storage_dir, "auto_memory.md")

        if not self.file_update:
            self.file_update = join(self.storage_dir, "file_update.md")

        makedirs(self.storage_dir, exist_ok=True)
        makedirs(self.sessions_dir, exist_ok=True)
        return self


class SecurityConfig(BaseModel):
    """安全相关配置"""

    check_enabled: bool = Field(default=True, description="是否启用安全检查")


class EngineConfig(BaseModel):
    """模型调用逻辑相关配置"""

    max_cycles: int = Field(default=20, description="最大循环次数")
    max_token: int = Field(default=200_000, description="会话上下文最大 token 数量")


class Config(BaseSettings):
    """主配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        cli_parse_args=True,
        env_nested_delimiter="__",
    )

    # 分组配置
    gate: GateConfig = Field(default_factory=GateConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)
