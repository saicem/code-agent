#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

import argparse
import os
from code_agent.context import global_context
from code_agent.config import config


from code_agent.agent import CodeAgent
from code_agent.contexts import (
    UserContextManager,
    ProjectContextManager,
    SessionContextManager,
)
from code_agent.commands import CommandHandler


def main():
    """主函数"""

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Code Agent")
    parser.add_argument(
        "--platform",
        type=str,
        choices=["bailian"],
        default="bailian",
        help="平台类型",
    )
    parser.add_argument("--model", type=str, required=True, help="模型名称")
    parser.add_argument("--output", type=str, help="输出文件路径")
    args = parser.parse_args()

    # 初始化 Code Agent
    try:
        agent = CodeAgent.create(platform=args.platform, model=args.model)
        print(f"Code Agent 已启动，使用平台: {args.platform}，模型: {args.model}")
    except ValueError as e:
        print(f"初始化失败: {e}")
        return

    # 初始化上下文管理器
    user_context = UserContextManager()
    project_context = ProjectContextManager(config.base_dir)
    session_context = SessionContextManager(platform=args.platform, model=args.model)

    # 将组件存储到全局上下文
    global_context.set_args(args)
    global_context.set_user_context(user_context)
    global_context.set_project_context(project_context)
    global_context.set_session_context(session_context)
    global_context.set_agent(agent)

    # 初始化指令处理器
    command_handler = CommandHandler()

    # 显示项目信息
    print("\n" + "=" * 50)
    print("项目上下文:")
    print(project_context.get_project_summary())
    print("=" * 50 + "\n")

    # 显示用户上下文
    user_summary = user_context.get_context_summary()
    if user_summary:
        print("用户上下文:")
        print(user_summary)
        print()

    print("请输入任务描述，输入 '/quit' 退出，输入 '/help' 查看可用指令")

    # 循环对话
    while True:
        task = input("\n任务: ")

        # 处理指令
        if command_handler.handle_command(task):
            if task == "/quit":
                break
            continue

        # 构建增强的提示词
        enhanced_prompt = _build_enhanced_prompt(
            task,
            user_context,
            project_context,
            session_context,
        )

        # 调用模型
        try:
            result = agent.execute_task(enhanced_prompt)
        except Exception as e:
            print(f"执行错误: {e}")
            continue

        print(f"\n结果:\n{result}")

        # 保存到会话上下文
        # 确保 result 是字符串类型
        result_str = str(result) if result else ""
        session_context.add_dialogue(task, result_str)

        # 更新用户上下文
        user_context.update_from_dialogue(task, result_str)

        # 将输出写入文件
        if args.output:
            try:
                with open(args.output, "a", encoding="utf-8") as f:
                    f.write(f"任务: {task}\n结果: {result}\n\n")
                print(f"\n结果已写入到 {args.output}")
            except Exception as e:
                print(f"写入文件失败: {e}")


def _build_enhanced_prompt(task, user_context, project_context, session_context):
    """构建增强的提示词

    Args:
        task: 任务描述
        user_context: 用户上下文管理器
        project_context: 项目上下文管理器
        session_context: 会话上下文管理器

    Returns:
        增强的提示词
    """
    prompt_parts = []

    # 添加用户上下文
    user_summary = user_context.get_context_summary()
    if user_summary:
        prompt_parts.append("用户上下文:")
        prompt_parts.append(user_summary)
        prompt_parts.append("")

    # 添加项目上下文
    project_summary = project_context.get_project_summary()
    if project_summary:
        prompt_parts.append("项目上下文:")
        prompt_parts.append(project_summary)
        prompt_parts.append("")

    # 添加会话上下文
    session_context_str = session_context.get_context()
    if session_context_str:
        prompt_parts.append("会话上下文:")
        prompt_parts.append(session_context_str)
        prompt_parts.append("")

    # 添加任务
    prompt_parts.append("任务:")
    prompt_parts.append(task)

    # 添加指令
    prompt_parts.append("")
    prompt_parts.append(
        "请根据以上上下文信息完成任务。如果需要修改代码，请使用以下格式："
    )
    prompt_parts.append("```language")
    prompt_parts.append("代码内容")
    prompt_parts.append("```")
    prompt_parts.append("并在代码块前说明要修改的文件名。")

    return "\n".join(prompt_parts)


if __name__ == "__main__":
    main()
