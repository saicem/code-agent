#!/usr/bin/env python3
"""
Code Agent 主入口文件
"""

import argparse
import os
from code_agent.agent import CodeAgent
from code_agent.user_context import UserContextManager
from code_agent.project_context import ProjectContextManager
from code_agent.session_context import SessionContextManager
from code_agent.rag import RAGManager
from code_agent.code_modifier import CodeModifier
from code_agent.commands import CommandHandler

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Code Agent")
    parser.add_argument("--platform", type=str, choices=["ollama", "bailian"], required=True,
                        help="平台类型")
    parser.add_argument("--model", type=str, required=True,
                        help="模型名称")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--project-dir", type=str, default=".", help="项目目录路径")
    parser.add_argument("--apply-changes", action="store_true", help="应用代码修改到文件")
    args = parser.parse_args()
    
    # 转化 project_dir 为绝对路径
    args.project_dir = os.path.abspath(args.project_dir)
    
    # 初始化 Code Agent
    try:
        agent = CodeAgent.create(platform=args.platform, model=args.model)
        print(f"Code Agent 已启动，使用平台: {args.platform}，模型: {args.model}")
    except ValueError as e:
        print(f"初始化失败: {e}")
        return
    
    # 初始化上下文管理器
    user_context = UserContextManager()
    project_context = ProjectContextManager(args.project_dir)
    session_context = SessionContextManager()
    rag_manager = RAGManager(project_context)
    code_modifier = CodeModifier(args.project_dir)
    
    # 初始化指令处理器
    command_handler = CommandHandler()
    
    # 显示项目信息
    print("\n" + "="*50)
    print("项目上下文:")
    print(project_context.get_project_summary())
    print("="*50 + "\n")
    
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
        if command_handler.handle_command(task, args=args):
            if task == '/quit':
                break
            continue
        
        # 构建增强的提示词
        enhanced_prompt = _build_enhanced_prompt(
            task,
            user_context,
            project_context,
            session_context,
            rag_manager
        )
        
        # 调用模型
        try:
            result = agent.execute_task(enhanced_prompt)
        except Exception as e:
            print(f"执行错误: {e}")
            continue
        
        print(f"\n结果:\n{result}")
        
        # 解析代码块
        code_blocks = code_modifier.parse_code_blocks(result)
        
        if code_blocks:
            print(f"\n检测到 {len(code_blocks)} 个代码块")
            
            # 确定目标文件
            targets = code_modifier.determine_target_files(code_blocks, task)
            
            print("将要修改的文件:")
            for target in targets:
                operation_text = {
                    "create": "创建",
                    "update": "更新",
                    "delete": "删除",
                    "append": "追加"
                }.get(target["operation"], target["operation"])
                temp_text = " (临时文件)" if target.get("is_temp", False) else ""
                print(f"  - {operation_text} {target['file_name']}{temp_text}")
            
            # 应用修改
            if args.apply_changes:
                print("\n应用修改...")
                results = code_modifier.apply_changes(targets)
                
                for result in results:
                    if result["success"]:
                        print(f"  ✓ {result['message']}")
                    else:
                        print(f"  ✗ {result['message']}")
                
                # 显示修改摘要
                print(f"\n{code_modifier.get_changes_summary()}")
            else:
                print("\n提示: 使用 --apply-changes 参数来实际应用这些修改")
        
        # 保存到会话上下文
        session_context.add_dialogue(task, result)
        
        # 更新用户上下文
        dialogue_history = session_context.get_recent_dialogues()
        user_context.update_from_dialogue(dialogue_history)
        
        # 将输出写入文件
        if args.output:
            try:
                with open(args.output, "a", encoding="utf-8") as f:
                    f.write(f"任务: {task}\n结果: {result}\n\n")
                print(f"\n结果已写入到 {args.output}")
            except Exception as e:
                print(f"写入文件失败: {e}")

def _build_enhanced_prompt(task, user_context, project_context, session_context, rag_manager):
    """构建增强的提示词
    
    Args:
        task: 任务描述
        user_context: 用户上下文管理器
        project_context: 项目上下文管理器
        session_context: 会话上下文管理器
        rag_manager: RAG 管理器
        
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
    
    # 添加相关文件上下文（RAG）
    retrieval_context = rag_manager.build_retrieval_context(task)
    if retrieval_context and retrieval_context != "未找到相关文件":
        prompt_parts.append("相关文件:")
        prompt_parts.append(retrieval_context)
        prompt_parts.append("")
    
    # 添加任务
    prompt_parts.append("任务:")
    prompt_parts.append(task)
    
    # 添加指令
    prompt_parts.append("")
    prompt_parts.append("请根据以上上下文信息完成任务。如果需要修改代码，请使用以下格式：")
    prompt_parts.append("```language")
    prompt_parts.append("代码内容")
    prompt_parts.append("```")
    prompt_parts.append("并在代码块前说明要修改的文件名。")
    
    return "\n".join(prompt_parts)

if __name__ == "__main__":
    main()