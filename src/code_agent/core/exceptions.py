class CodeAgentError(Exception):
    """所有自定义异常的基类"""

    code: str = "UNKNOWN_ERROR"
    message: str = "An unknown error occurred"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)


class ToolError(CodeAgentError):
    """工具执行异常"""

    code = "TOOL_ERROR"
    message = "Tool execution failed"


class ConfigurationError(CodeAgentError):
    """配置异常"""

    code = "CONFIG_ERROR"
    message = "Invalid configuration"


class SessionError(CodeAgentError):
    """会话异常"""

    code = "SESSION_ERROR"
    message = "Session operation failed"


class SystemError(CodeAgentError):
    """系统异常基类"""

    code = "SYSTEM_ERROR"
    message = "System exception"
