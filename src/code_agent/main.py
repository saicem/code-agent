#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

from code_agent.prompt import system_prompt

from code_agent.dependency import (
    MEMORY_MANAGER,
    SESSION_MANAGER,
    COMMAND_HANDLER,
    CONFIG,
    CURRENT_SESSION,
)
from code_agent.agent import CodeAgent


def main():
    CURRENT_SESSION.set(
        SESSION_MANAGER.load_last_session() or SESSION_MANAGER.create_session()
    )
    agent = CodeAgent(CONFIG.api_key, CONFIG.base_url)
    print("Code Agent 已启动")
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

        if COMMAND_HANDLER.handle_command(task):
            continue

        session = CURRENT_SESSION.get()
        session.set_system_prompt(system_prompt)
        session.add_user_message(task)

        # 调用模型
        try:
            result = agent.execute_task(session)
            print(f"\n结果:\n{result}")
        except Exception as e:
            print(f"执行错误: {e}")
            continue

        SESSION_MANAGER.save_session(session)
        # MEMORY_MANAGER.add_history(f"任务: {task[:30]}... -> 已完成")


if __name__ == "__main__":
    main()
