#!/usr/bin/env python3
"""
指令处理模块
"""

from typing import Dict, Callable, Any


class CommandHandler:
    """指令处理器类"""
    
    def __init__(self):
        """初始化指令处理器"""
        self.commands = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        """注册默认指令"""
        self.register_command("/quit", self._handle_quit, "退出程序")
        self.register_command("/about", self._handle_about, "显示当前信息")
        self.register_command("/help", self._handle_help, "查看可用指令")
    
    def register_command(self, command: str, handler: Callable, description: str):
        """注册新指令
        
        Args:
            command: 指令名称，如 "/quit"
            handler: 指令处理函数
            description: 指令描述
        """
        self.commands[command] = {
            "handler": handler,
            "description": description
        }
    
    def unregister_command(self, command: str):
        """注销指令
        
        Args:
            command: 指令名称
        """
        if command in self.commands:
            del self.commands[command]
    
    def handle_command(self, command: str, **kwargs) -> bool:
        """处理指令
        
        Args:
            command: 指令字符串
            **kwargs: 传递给处理函数的参数
            
        Returns:
            是否是指令并已处理
        """
        # 检查是否是指令
        if not command.startswith("/"):
            return False
        
        # 查找指令处理器
        if command in self.commands:
            handler_info = self.commands[command]
            handler = handler_info["handler"]
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"执行指令出错: {e}")
            return True
        else:
            print(f"未知指令: {command}")
            print("可用指令:")
            for cmd, info in self.commands.items():
                print(f"  {cmd}: {info['description']}")
            return True
    
    def _handle_quit(self, **kwargs):
        """处理 /quit 指令"""
        # 这里不需要做任何事情，因为主循环会捕获 'exit' 或 '/quit'
        pass
    
    def _handle_help(self, **kwargs):
        """处理 /help 指令"""
        print("\n可用指令:")
        # 按字母序排列指令
        sorted_commands = sorted(self.commands.items())
        for cmd, info in sorted_commands:
            print(f"  {cmd}: {info['description']}")
    
    def _handle_about(self, **kwargs):
        """处理 /about 指令"""
        args = kwargs.get("args", None)
        if args:
            print("\nCode Agent 信息:")
            print(f"版本: 0.1.0")
            print(f"平台: {args.platform}")
            print(f"模型: {args.model}")
            print(f"项目目录: {args.project_dir}")
            print(f"应用修改: {'开启' if args.apply_changes else '关闭'}")
            if args.output:
                print(f"输出文件: {args.output}")
    
    def get_available_commands(self) -> Dict[str, str]:
        """获取可用指令列表
        
        Returns:
            指令名称到描述的映射
        """
        return {cmd: info["description"] for cmd, info in self.commands.items()}
