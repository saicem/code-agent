#!/usr/bin/env python3
"""
代码修改应用模块
"""

import os
import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CodeBlock:
    """代码块数据类"""

    language: str
    code: str
    type: str


@dataclass
class TargetFile:
    """目标文件数据类"""

    file_name: str
    code: str
    language: str
    operation: str
    is_temp: bool = False


@dataclass
class ApplyResult:
    """应用结果数据类"""

    file_name: str
    operation: str
    success: bool
    message: str
    is_temp: bool = False


@dataclass
class ChangeRecord:
    """修改记录数据类"""

    file: str
    operation: str
    is_temp: bool = False


class CodeModifier:
    """代码修改应用类"""

    def __init__(self, project_dir: str = "."):
        """初始化代码修改器

        Args:
            project_dir: 项目目录路径
        """
        self.project_dir = Path(project_dir)
        self.changes_applied = []

    def parse_code_blocks(self, response: str) -> list[CodeBlock]:
        """解析响应中的代码块

        Args:
            response: 模型响应字符串

        Returns:
            代码块列表
        """
        code_blocks = []

        # 匹配 ```language 格式的代码块
        pattern = r"```(\w+)?\n([\s\S]*?)\n```"
        matches = re.finditer(pattern, response, re.DOTALL)

        for match in matches:
            language: str = match.group(1) or "text"
            code: str = match.group(2).strip()

            code_blocks.append(
                CodeBlock(language=language, code=code, type="code_block")
            )

        # 如果没有找到代码块，尝试匹配其他格式
        if not code_blocks:
            # 匹配 def class 等关键字开头的代码
            lines = response.split("\n")
            current_code = []
            in_code = False
            indent_level = None

            for line in lines:
                stripped = line.lstrip()

                # 检测代码开始
                if stripped.startswith(
                    ("def ", "class ", "import ", "from ", "async def ")
                ):
                    if current_code:
                        code_blocks.append(
                            CodeBlock(
                                language="python",
                                code="\n".join(current_code),
                                type="indented_code",
                            )
                        )
                        current_code = []
                    in_code = True
                    indent_level = len(line) - len(line.lstrip())

                # 检测代码结束
                elif (
                    in_code
                    and stripped
                    and not line.startswith(" " * (indent_level or 0))
                ):
                    if current_code:
                        code_blocks.append(
                            CodeBlock(
                                language="python",
                                code="\n".join(current_code),
                                type="indented_code",
                            )
                        )
                        current_code = []
                    in_code = False

                # 收集代码行
                if in_code:
                    current_code.append(line)

            # 添加最后的代码块
            if current_code:
                code_blocks.append(
                    CodeBlock(
                        language="python",
                        code="\n".join(current_code),
                        type="indented_code",
                    )
                )

        return code_blocks

    def determine_target_files(
        self, code_blocks: list[CodeBlock], task: str
    ) -> list[TargetFile]:
        """确定目标文件

        Args:
            code_blocks: 代码块列表
            task: 任务描述

        Returns:
            目标文件信息列表
        """
        targets = []

        for code_block in code_blocks:
            # 从任务描述中提取文件名
            file_name = self._extract_filename_from_task(task, code_block)

            if file_name:
                targets.append(
                    TargetFile(
                        file_name=file_name,
                        code=code_block.code,
                        language=code_block.language,
                        operation=self._determine_operation(task),
                    )
                )
            else:
                # 如果没有明确的文件名，创建临时文件
                temp_name = self._generate_temp_filename(code_block.language)
                targets.append(
                    TargetFile(
                        file_name=temp_name,
                        code=code_block.code,
                        language=code_block.language,
                        operation=self._determine_operation(task),
                        is_temp=True,
                    )
                )

        return targets

    def _extract_filename_from_task(
        self, task: str, code_block: CodeBlock
    ) -> str | None:
        """从任务描述中提取文件名

        Args:
            task: 任务描述
            code_block: 代码块

        Returns:
            文件名或 None
        """
        # 匹配 "文件名.扩展名" 格式
        pattern = r"[\w\-_]+\.[a-zA-Z]+"
        matches = re.findall(pattern, task)

        if matches:
            # 返回第一个匹配的文件名
            return matches[0]

        # 匹配 "文件名" 格式
        pattern = r"文件[名]?\s*[:：]?\s*([\w\-_]+)"
        matches = re.findall(pattern, task)

        if matches:
            # 根据代码块语言添加扩展名
            filename = matches[0]
            ext = self._get_extension_from_language(code_block.language)
            return f"{filename}{ext}"

        return None

    def _get_extension_from_language(self, language: str) -> str:
        """根据语言获取扩展名

        Args:
            language: 编程语言

        Returns:
            文件扩展名
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "c++": ".cpp",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "xml": ".xml",
            "sql": ".sql",
            "bash": ".sh",
            "shell": ".sh",
            "text": ".txt",
        }

        return extensions.get(language.lower(), ".txt")

    def _generate_temp_filename(self, language: str) -> str:
        """生成临时文件名

        Args:
            language: 编程语言

        Returns:
            临时文件名
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self._get_extension_from_language(language)
        return f"generated_{timestamp}{ext}"

    def _determine_operation(self, task: str) -> str:
        """确定操作类型

        Args:
            task: 任务描述

        Returns:
            操作类型
        """
        task_lower = task.lower()

        if "创建" in task_lower or "新建" in task_lower or "生成" in task_lower:
            return "create"
        elif "修改" in task_lower or "更新" in task_lower or "改" in task_lower:
            return "update"
        elif "删除" in task_lower or "移除" in task_lower:
            return "delete"
        elif "添加" in task_lower or "增加" in task_lower:
            return "append"
        else:
            return "create"

    def apply_changes(
        self, targets: list[TargetFile], dry_run: bool = False
    ) -> list[ApplyResult]:
        """应用代码修改

        Args:
            targets: 目标文件列表
            dry_run: 是否为试运行（不实际修改文件）

        Returns:
            应用结果列表
        """
        results = []

        for target in targets:
            file_name = target.file_name
            code = target.code
            operation = target.operation
            is_temp = target.is_temp

            result = ApplyResult(
                file_name=file_name,
                operation=operation,
                success=False,
                message="",
                is_temp=is_temp,
            )

            try:
                file_path = self.project_dir / file_name

                if operation == "create":
                    # 创建新文件
                    if not dry_run:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(code)
                    result.success = True
                    result.message = f"已创建文件: {file_name}"

                elif operation == "update":
                    # 更新现有文件
                    if file_path.exists():
                        if not dry_run:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(code)
                        result.success = True
                        result.message = f"已更新文件: {file_name}"
                    else:
                        result.message = f"文件不存在: {file_name}"

                elif operation == "append":
                    # 追加到文件
                    if file_path.exists():
                        if not dry_run:
                            with open(file_path, "a", encoding="utf-8") as f:
                                f.write("\n" + code)
                        result.success = True
                        result.message = f"已追加到文件: {file_name}"
                    else:
                        result.message = f"文件不存在: {file_name}"

                elif operation == "delete":
                    # 删除文件
                    if file_path.exists():
                        if not dry_run:
                            os.remove(file_path)
                        result.success = True
                        result.message = f"已删除文件: {file_name}"
                    else:
                        result.message = f"文件不存在: {file_name}"

                else:
                    result.message = f"不支持的操作: {operation}"

                if result.success:
                    self.changes_applied.append(
                        ChangeRecord(
                            file=file_name, operation=operation, is_temp=is_temp
                        )
                    )

            except Exception as e:
                result.message = f"操作失败: {str(e)}"

            results.append(result)

        return results

    def get_changes_summary(self) -> str:
        """获取修改摘要

        Returns:
            修改摘要字符串
        """
        if not self.changes_applied:
            return "未应用任何修改"

        summary_parts = ["已应用的修改:"]

        for change in self.changes_applied:
            file_name = change.file
            operation = change.operation
            is_temp = change.is_temp

            operation_text = {
                "create": "创建",
                "update": "更新",
                "delete": "删除",
                "append": "追加",
            }.get(operation, operation)

            temp_text = " (临时文件)" if is_temp else ""
            summary_parts.append(f"  - {operation_text} {file_name}{temp_text}")

        return "\n".join(summary_parts)

    def clear_history(self) -> None:
        """清空修改历史"""
        self.changes_applied = []
