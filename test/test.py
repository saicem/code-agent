#!/usr/bin/env python3
"""
测试脚本
"""

print("开始测试")

# 测试导入
print("测试导入...")
try:
    from code_agent.agent import CodeAgent
    print("导入成功")
except Exception as e:
    print(f"导入失败: {e}")

# 测试初始化
print("\n测试初始化...")
try:
    agent = CodeAgent(platform='ollama', model='Qwen3.5')
    print("初始化成功")
except Exception as e:
    print(f"初始化失败: {e}")

# 测试执行任务
print("\n测试执行任务...")
try:
    result = agent.execute_task('编写一个 Python 函数，计算斐波那契数列的第 n 项')
    print(f"执行结果: {result}")
except Exception as e:
    print(f"执行失败: {e}")
