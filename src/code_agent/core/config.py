#!/usr/bin/env python3
"""
配置管理模块
将配置项分组到不同的配置类中，便于不同模块精确传入所需配置
"""

from os import makedirs
from os.path import abspath, join

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


class ContextConfig(BaseModel):
    """上下文相关配置"""

    max_dialogues: int = Field(default=10, description="会话上下文最大对话数量")
    context_file: str = Field(default="", description="会话上下文文件路径")


class SecurityConfig(BaseModel):
    """安全相关配置"""

    check_enabled: bool = Field(default=True, description="是否启用安全检查")


class LoggingConfig(BaseModel):
    """日志相关配置"""

    otlp_enabled: bool = Field(default=False, description="是否启用 OTLP 导出器")


class EngineConfig(BaseModel):
    """模型调用逻辑相关配置"""

    max_cycles: int = Field(default=20, description="最大循环次数")
    max_token: int = Field(default=8000, description="会话上下文最大 token 数量")


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
    context: ContextConfig = Field(default_factory=ContextConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)

    @model_validator(mode="after")
    def _post_init(self) -> "Config":
        """初始化后处理：填充依赖路径并确保目录存在"""
        self._fill_dependent_paths()
        self._ensure_directories()
        return self

    def _fill_dependent_paths(self):
        """填充依赖于其他配置项的路径"""
        # 存储目录
        if not self.storage.storage_dir:
            self.storage.storage_dir = abspath(join(self.storage.base_dir, ".memo"))

        # 会话目录
        if not self.storage.sessions_dir:
            self.storage.sessions_dir = join(self.storage.storage_dir, "sessions")

        # 上下文文件
        if not self.context.context_file:
            self.context.context_file = join(self.storage.storage_dir, "session_context.json")

    def _ensure_directories(self):
        """确保必要的目录存在"""
        makedirs(self.storage.storage_dir, exist_ok=True)
        makedirs(self.storage.sessions_dir, exist_ok=True)


_config = Config()


def get_config() -> Config:
    return _config
