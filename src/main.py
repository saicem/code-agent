#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

import asyncio

import code_agent._setup  # noqa: F401
from code_agent.agent.app import start_agent
from code_agent.core.container import Container


def main() -> None:
    """同步入口函数，用于脚本调用"""
    container = Container()
    container.wire(packages=["code_agent"])
    asyncio.run(start_agent())


if __name__ == "__main__":
    main()
