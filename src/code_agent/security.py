#!/usr/bin/env python3
"""
安全管理模块
"""

import re

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        """初始化安全管理器"""
        # 不安全的命令和操作
        self.dangerous_patterns = [
            r'rm\s+-rf',  # 危险的删除命令
            r'sudo\s+',   #  sudo 命令
            r'eval\s*\(',  # eval 函数
            r'exec\s*\(',  # exec 函数
            r'os\.system', # 系统命令执行
            r'subprocess\.', # 子进程执行
            r'__import__',   # 动态导入
            r'open\s*\(.*\,\s*["\']w["\']', # 写入文件
            r'open\s*\(.*\,\s*["\']a["\']', # 追加文件
            r'del\s+',     # 删除变量
            r'globals\(\)', # 全局变量
            r'locals\(\)',  # 局部变量
            r'vars\(\)',    # 变量
        ]
    
    def check_task(self, task):
        """检查任务是否安全
        
        Args:
            task: 任务描述
            
        Returns:
            是否安全
        """
        task_lower = task.lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, task_lower):
                return False
        
        return True
    
    def sanitize_input(self, input_data):
        """清理输入
        
        Args:
            input_data: 输入数据
            
        Returns:
            清理后的输入
        """
        # 移除潜在的危险字符
        dangerous_chars = [';', '|', '&', '>', '<', '`', '$', '!']
        for char in dangerous_chars:
            input_data = input_data.replace(char, '')
        
        return input_data
    
    def validate_code(self, code):
        """验证代码是否安全
        
        Args:
            code: 代码字符串
            
        Returns:
            (是否安全, 错误消息)
        """
        code_lower = code.lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code_lower):
                return False, f"代码包含不安全操作: {pattern}"
        
        return True, ""
