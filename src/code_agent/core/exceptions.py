class ToolException(Exception):
    """工具异常基类"""

    message: str = "工具使用异常"


class SystemException(Exception):
    """系统异常基类"""

    message: str = "系统异常"
