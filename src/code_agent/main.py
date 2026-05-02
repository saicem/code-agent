#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

from code_agent.helpers.otlp import init_otlp
import logging


import traceback
from code_agent.prompt import system_prompt
from code_agent.dependency import (
    MEMORY_MANAGER,
    SESSION_MANAGER,
    COMMAND_HANDLER,
    CONFIG,
    CURRENT_SESSION,
)
from code_agent.agent import CodeAgent

file_handler = logging.FileHandler(CONFIG.log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


def main():
    if CONFIG.otlp_enabled:
        init_otlp()
    logger.info("========== Code Agent 启动中 ==========")
    try:
        # 加载或创建会话
        logger.debug("加载最后会话...")
        session = SESSION_MANAGER.load_last_session()
        if session:
            logger.info(f"已加载会话: {session.session_id}")
        else:
            session = SESSION_MANAGER.create_session()
            logger.info(f"创建新会话: {session.session_id}")
        CURRENT_SESSION.set(session)

        # 初始化 Agent
        logger.debug("初始化 CodeAgent...")
        agent = CodeAgent(CONFIG.api_key, CONFIG.base_url)
        logger.info("Code Agent 初始化完成")

        print("\n" + "=" * 50)
        print("记忆摘要:")
        print(MEMORY_MANAGER.get_summary())
        print("=" * 50 + "\n")
        print("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令")

        # 循环对话
        while True:
            task = input("\n任务: ")

            if task.strip() == "":
                continue

            # 处理命令
            if COMMAND_HANDLER.handle_command(task):
                logger.debug(f"已处理命令: {task}")
                continue

            # 执行任务
            session = CURRENT_SESSION.get()
            session.set_system_prompt(system_prompt)
            session.add_user_message(task)

            try:
                logger.debug(f"开始执行任务: {task[:50]}...")
                result = agent.execute_task(session)
                logger.info("任务执行成功")
                print(f"\n结果:\n{result}")
            except Exception as e:
                logger.error(f"任务执行失败: {e}", exc_info=True)
                print(f"执行错误: {e}")
                continue

            # 保存会话
            logger.debug("保存会话...")
            SESSION_MANAGER.save_session(session)
            logger.debug("会话保存成功")

    except Exception as e:
        logger.critical(f"Code Agent 启动失败: {e}", exc_info=True)
        print(f"启动错误: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
