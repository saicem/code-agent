#!/usr/bin/env python3
"""
写入工具
用于写入文件内容
"""

import os
import json
from pydantic import BaseModel, Field, ValidationError
from code_agent.tools.base_tool import BaseTool
from code_agent.tools.tool_manager import ToolManager


class WriteParams(BaseModel):
    """Write 工具参数模型"""

    file_path: str = Field(..., description="文件路径，相对于项目根目录")
    content: str = Field(..., description="要写入的文件内容")
    overwrite: bool = Field(True, description="是否覆盖现有文件，默认为 True")


@ToolManager.register_tool(
    name="write_file",
    description="写入文件内容到指定路径。当你需要创建或修改文件时使用此工具。",
    param_type=WriteParams,
)
class WriteTool(BaseTool):
    """写入工具"""

    def __init__(self, base_dir: str = "."):
        """初始化写入工具

        Args:
            base_dir: 基础目录
        """
        self.base_dir = os.path.abspath(base_dir)

    def run(self, params: str) -> str:
        """运行工具

        Args:
            params: JSON 格式的参数字符串

        Returns:
            JSON 格式的结果字符串
        """
        try:
            # 使用 Pydantic 验证参数
            try:
                validated_params = WriteParams.model_validate_json(params)
            except ValidationError as e:
                return json.dumps(
                    {"success": False, "message": f"参数验证失败: {str(e)}"},
                    ensure_ascii=False,
                )

            # 构建完整路径
            full_path = os.path.join(self.base_dir, validated_params.file_path)
            full_path = os.path.abspath(full_path)

            # 确保路径在基础目录内
            if not full_path.startswith(self.base_dir):
                return json.dumps(
                    {"success": False, "message": "文件路径超出允许范围"},
                    ensure_ascii=False,
                )

            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # 检查文件是否存在
            if os.path.exists(full_path) and not validated_params.overwrite:
                return json.dumps(
                    {"success": False, "message": "文件已存在，且 overwrite 为 False"},
                    ensure_ascii=False,
                )

            # 写入文件
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(validated_params.content)

            return json.dumps(
                {
                    "success": True,
                    "message": f"文件写入成功: {validated_params.file_path}",
                    "file_path": validated_params.file_path,
                },
                ensure_ascii=False,
            )

        except json.JSONDecodeError as e:
            return json.dumps(
                {"success": False, "message": f"JSON 解析失败: {str(e)}"},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"success": False, "message": f"写入文件失败: {str(e)}"},
                ensure_ascii=False,
            )
