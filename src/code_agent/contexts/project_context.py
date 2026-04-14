#!/usr/bin/env python3
"""
项目上下文管理模块
分析工作目录的文件结构、各部分作用和技术栈
"""

import os
import json
from pathlib import Path
from code_agent.config import config
from code_agent.file_ignore import FileIgnoreManager


class ProjectContextManager:
    """项目上下文管理类"""

    def __init__(self, project_dir: str = "."):
        """初始化项目上下文管理器

        Args:
            project_dir: 项目目录路径
        """
        self.project_dir = Path(project_dir).resolve()
        self.context_file = Path(config.project_context_file)
        self.ignore_manager = FileIgnoreManager(str(self.project_dir))
        self.context = self._load_context()

    def _load_context(self) -> dict:
        """加载项目上下文

        Returns:
            项目上下文字典
        """
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_context(self) -> None:
        """保存项目上下文"""
        try:
            self.context_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def analyze_project(self) -> None:
        """分析项目结构和技术栈"""
        # 检查项目是否变化
        current_hash = self._calculate_project_hash()
        if self.context.get("hash") == current_hash:
            return

        # 分析项目
        file_structure = self._analyze_file_structure()
        tech_stack = self._detect_tech_stack(file_structure)
        directory_analysis = self._analyze_directories(file_structure)

        # 更新上下文
        self.context = {
            "hash": current_hash,
            "file_structure": file_structure,
            "tech_stack": tech_stack,
            "directory_analysis": directory_analysis,
            "project_name": self.project_dir.name,
        }

        self._save_context()

    def _calculate_project_hash(self) -> str:
        """计算项目哈希值

        Returns:
            项目哈希值
        """
        import hashlib

        hash_obj = hashlib.md5()
        for root, dirs, files in os.walk(self.project_dir):
            # 过滤忽略的目录
            dirs[:] = [
                d
                for d in dirs
                if not self.ignore_manager.is_ignored(os.path.join(root, d))
            ]

            for filename in files:
                file_path = os.path.join(root, filename)
                if not self.ignore_manager.is_ignored(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            while chunk := f.read(8192):
                                hash_obj.update(chunk)
                    except Exception:
                        continue

        return hash_obj.hexdigest()

    def _analyze_file_structure(self) -> dict:
        """分析文件结构

        Returns:
            文件结构字典
        """
        structure = {"directories": {}, "files": []}

        for root, dirs, files in os.walk(self.project_dir):
            # 过滤忽略的目录
            dirs[:] = [
                d
                for d in dirs
                if not self.ignore_manager.is_ignored(os.path.join(root, d))
            ]

            for dirname in dirs:
                dir_path = os.path.join(root, dirname)
                if not self.ignore_manager.is_ignored(dir_path):
                    relative_path = os.path.relpath(dir_path, self.project_dir)
                    structure["directories"][relative_path] = self._get_directory_info(
                        dir_path
                    )

            for filename in files:
                file_path = os.path.join(root, filename)
                if not self.ignore_manager.is_ignored(file_path):
                    relative_path = os.path.relpath(file_path, self.project_dir)
                    structure["files"].append(
                        self._get_file_info(file_path, relative_path)
                    )

        return structure

    def _get_directory_info(self, dir_path: str) -> dict:
        """获取目录信息

        Args:
            dir_path: 目录路径

        Returns:
            目录信息字典
        """
        files_count = 0
        subdirs_count = 0

        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    files_count += 1
                elif os.path.isdir(item_path):
                    subdirs_count += 1
        except Exception:
            pass

        return {
            "files_count": files_count,
            "subdirs_count": subdirs_count,
            "description": self._infer_directory_purpose(dir_path),
        }

    def _get_file_info(self, file_path: str, relative_path: str) -> dict:
        """获取文件信息

        Args:
            file_path: 文件路径
            relative_path: 相对路径

        Returns:
            文件信息字典
        """
        try:
            file_stat = os.stat(file_path)
            file_ext = os.path.splitext(relative_path)[1].lower()

            return {
                "path": relative_path,
                "size": file_stat.st_size,
                "extension": file_ext,
                "modified": file_stat.st_mtime,
            }
        except Exception:
            return {
                "path": relative_path,
                "size": 0,
                "extension": "",
                "modified": 0,
            }

    def _infer_directory_purpose(self, dir_path: str) -> str:
        """推断目录用途

        Args:
            dir_path: 目录路径

        Returns:
            目录用途描述
        """
        dirname = os.path.basename(dir_path).lower()

        # 常见目录用途推断
        purpose_map = {
            "src": "源代码目录",
            "source": "源代码目录",
            "lib": "库文件目录",
            "libs": "库文件目录",
            "test": "测试文件目录",
            "tests": "测试文件目录",
            "docs": "文档目录",
            "doc": "文档目录",
            "examples": "示例代码目录",
            "example": "示例代码目录",
            "scripts": "脚本目录",
            "script": "脚本目录",
            "tools": "工具目录",
            "tool": "工具目录",
            "utils": "工具函数目录",
            "util": "工具函数目录",
            "config": "配置文件目录",
            "configs": "配置文件目录",
            "assets": "资源文件目录",
            "asset": "资源文件目录",
            "static": "静态资源目录",
            "templates": "模板目录",
            "template": "模板目录",
            "views": "视图目录",
            "view": "视图目录",
            "controllers": "控制器目录",
            "controller": "控制器目录",
            "models": "数据模型目录",
            "model": "数据模型目录",
            "services": "服务目录",
            "service": "服务目录",
            "api": "API 目录",
            "routes": "路由目录",
            "route": "路由目录",
            "middleware": "中间件目录",
            "handlers": "处理器目录",
            "handler": "处理器目录",
        }

        return purpose_map.get(dirname, "普通目录")

    def _detect_tech_stack(self, file_structure: dict) -> list[str]:
        """检测技术栈

        Args:
            file_structure: 文件结构

        Returns:
            技术栈列表
        """
        tech_stack = []

        # 根据文件扩展名检测技术栈
        extensions = set()
        for file_info in file_structure.get("files", []):
            ext = file_info.get("extension", "")
            if ext:
                extensions.add(ext)

        # 检测编程语言
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".cs": "C#",
        }

        for ext, lang in language_map.items():
            if ext in extensions:
                tech_stack.append(lang)

        # 检测框架和工具
        framework_map = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "Pipfile": "Python (Pipenv)",
            "pyproject.toml": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java (Gradle)",
            "composer.json": "PHP",
            "Gemfile": "Ruby",
        }

        for file_info in file_structure.get("files", []):
            filename = os.path.basename(file_info.get("path", ""))
            if filename in framework_map:
                tech_stack.append(framework_map[filename])

        # 检测 Web 框架
        web_frameworks = []
        if ".vue" in extensions:
            web_frameworks.append("Vue.js")
        if ".jsx" in extensions or ".tsx" in extensions:
            web_frameworks.append("React")
        if ".svelte" in extensions:
            web_frameworks.append("Svelte")

        tech_stack.extend(web_frameworks)

        # 去重并返回
        return list(dict.fromkeys(tech_stack))

    def _analyze_directories(self, file_structure: dict) -> dict:
        """分析目录结构

        Args:
            file_structure: 文件结构

        Returns:
            目录分析字典
        """
        analysis = {}

        for dir_path, dir_info in file_structure.get("directories", {}).items():
            analysis[dir_path] = {
                "purpose": dir_info.get("description", "普通目录"),
                "files_count": dir_info.get("files_count", 0),
                "subdirs_count": dir_info.get("subdirs_count", 0),
            }

        return analysis

    def get_project_summary(self) -> str:
        """获取项目摘要

        Returns:
            项目摘要字符串
        """
        if not self.context:
            return "项目为空或未分析"

        summary_parts = []

        # 项目名称
        project_name = self.context.get("project_name", "未知项目")
        summary_parts.append(f"项目名称: {project_name}")

        # 技术栈
        tech_stack = self.context.get("tech_stack", [])
        if tech_stack:
            summary_parts.append(f"技术栈: {', '.join(tech_stack)}")

        # 文件统计
        file_structure = self.context.get("file_structure", {})
        assert isinstance(file_structure, dict), "file_structure should be a dict"
        files_count = len(file_structure.get("files", []))
        dirs_count = len(file_structure.get("directories", {}))
        summary_parts.append(f"文件数量: {files_count} 个文件，{dirs_count} 个目录")

        # 主要目录
        directory_analysis = self.context.get("directory_analysis", {})
        assert isinstance(directory_analysis, dict), (
            "directory_analysis should be a dict"
        )
        if directory_analysis:
            summary_parts.append("\n主要目录:")
            for dir_path, dir_info in directory_analysis.items():
                purpose = dir_info.get("purpose", "普通目录")
                files_count = dir_info.get("files_count", 0)
                summary_parts.append(
                    f"  - {dir_path}: {purpose} ({files_count} 个文件)"
                )

        return "\n".join(summary_parts)

    def get_context_summary(self) -> str:
        """获取上下文摘要

        Returns:
            上下文摘要字符串
        """
        return self.get_project_summary()

    def search_files(self, query: str, limit: int = 5) -> list:
        """搜索文件

        Args:
            query: 搜索查询
            limit: 返回结果限制

        Returns:
            匹配的文件列表
        """
        query_lower = query.lower()
        results = []

        file_structure = self.context.get("file_structure", {})
        assert isinstance(file_structure, dict), "file_structure should be a dict"
        files = file_structure.get("files", [])
        assert isinstance(files, list), "files should be a list"

        for file_info in files:
            # 在文件名中搜索
            if query_lower in file_info.get("path", "").lower():
                results.append(file_info)
                if len(results) >= limit:
                    break

            # 在文件扩展名中搜索
            elif query_lower in file_info.get("extension", "").lower():
                results.append(file_info)
                if len(results) >= limit:
                    break

        return results

    def get_file_content(self, file_path: str) -> str | None:
        """获取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容或 None
        """
        # 转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.project_dir, file_path)

        # 检查文件是否在项目中
        try:
            relative_path = os.path.relpath(file_path, self.project_dir)
            if relative_path.startswith(".."):
                return None
        except Exception:
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def clear_context(self) -> None:
        """清空项目上下文"""
        self.context = {}
        self._save_context()
