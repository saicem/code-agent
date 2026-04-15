#!/usr/bin/env python3
"""
上下文管理模块
用于存储和管理共享变量
"""


class GlobalContext:
    """全局上下文类"""

    def __init__(self):
        """初始化全局上下文"""
        self.args = None
        self.user_context = None
        self.project_context = None
        self.session_context = None
        self.agent = None

    def set_args(self, args):
        """设置命令行参数

        Args:
            args: 命令行参数对象
        """
        self.args = args

    def set_user_context(self, user_context):
        """设置用户上下文

        Args:
            user_context: 用户上下文实例
        """
        self.user_context = user_context

    def set_project_context(self, project_context):
        """设置项目上下文

        Args:
            project_context: 项目上下文实例
        """
        self.project_context = project_context

    def set_session_context(self, session_context):
        """设置会话上下文

        Args:
            session_context: 会话上下文实例
        """
        self.session_context = session_context

    def set_agent(self, agent):
        """设置 Agent 实例

        Args:
            agent: Agent 实例
        """
        self.agent = agent


# 创建全局上下文实例
global_context = GlobalContext()
