#!/usr/bin/env python3
"""
依赖注入容器模块
使用 dependency-injector 管理项目依赖
"""

from dependency_injector import containers, providers

from code_agent.agent.gate import GenAiGate
from code_agent.agent.memory import MemoryManager
from code_agent.agent.session_manager import SessionManager
from code_agent.core.config import Config


class Container(containers.DeclarativeContainer):
    """核心依赖容器"""

    # 配置 - 使用 lambda 延迟创建，确保配置正确初始化
    config: providers.Singleton[Config] = providers.Singleton(Config)

    # 记忆服务
    memory_manager: providers.Singleton[MemoryManager] = providers.Singleton(
        MemoryManager,
        config=config,
    )

    session_manager: providers.Singleton[SessionManager] = providers.Singleton(
        SessionManager,
        sessions_dir=config().storage.sessions_dir,
        memory_manager=memory_manager,
    )

    gate: providers.Factory[GenAiGate] = providers.Factory(
        GenAiGate,
        config=config().gate,
    )
