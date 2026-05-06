#!/usr/bin/env python3
"""
依赖注入容器模块
使用 dependency-injector 管理项目依赖
"""

from dependency_injector import containers, providers

from code_agent.agent.gate import GenAiGate
from code_agent.agent.session_manager import SessionManager
from code_agent.core.config import Config

_config = Config()


class Container(containers.DeclarativeContainer):
    """核心依赖容器"""

    # 配置 - 使用 lambda 延迟创建，确保配置正确初始化
    config: providers.Singleton[Config] = providers.Singleton(lambda _config: _config)

    # 会话管理器 - 使用 lambda 获取嵌套属性
    session_manager: providers.Singleton[SessionManager] = providers.Singleton(
        SessionManager,
        sessions_dir=_config.storage.sessions_dir,
    )

    # AI 网关 - 传递 GateConfig（config.gate）而不是整个 Config
    gate: providers.Factory[GenAiGate] = providers.Factory(
        GenAiGate,
        config=_config.gate,
    )
