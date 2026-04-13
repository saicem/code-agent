#!/usr/bin/env python3
"""
项目上下文管理模块
"""

import os
import hashlib
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class ProjectContextManager:
    """项目上下文管理类"""
    
    def __init__(self, project_dir: str = ".", context_file: str = ".memo/project_context.json"):
        """初始化项目上下文管理器
        
        Args:
            project_dir: 项目目录路径
            context_file: 上下文文件路径
        """
        # 确保 .memo 目录存在
        os.makedirs(".memo", exist_ok=True)
        self.project_dir = Path(project_dir)
        self.context_file = context_file
        self.context = self._load_context()
        self.file_index = self.context.get("file_index", {})
        self.last_hash = self.context.get("last_hash", "")
        
        # 检查文件是否变化
        self._check_file_changes()
    
    def _load_context(self) -> Dict[str, Any]:
        """加载项目上下文
        
        Returns:
            项目上下文字典
        """
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_context(self) -> None:
        """保存项目上下文"""
        self.context["file_index"] = self.file_index
        self.context["last_hash"] = self.last_hash
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _calculate_directory_hash(self) -> str:
        """计算目录的哈希值，用于检测变化
        
        Returns:
            目录哈希值
        """
        hash_obj = hashlib.md5()
        
        # 遍历目录中的文件
        for file_path in self._get_project_files():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        hash_obj.update(chunk)
            except Exception:
                continue
        
        return hash_obj.hexdigest()
    
    def _get_project_files(self) -> List[str]:
        """获取项目中的所有文件
        
        Returns:
            文件路径列表
        """
        # 忽略的目录和文件
        ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", ".vscode", ".idea", ".memo"}
        ignore_files = {".gitignore", ".DS_Store", "project_context.json", "user_context.json", "memory.json", "agent.log"}
        
        files = []
        for root, dirs, filenames in os.walk(self.project_dir):
            # 移除忽略的目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for filename in filenames:
                if filename not in ignore_files:
                    file_path = os.path.join(root, filename)
                    if os.path.isfile(file_path):
                        files.append(file_path)
        
        return files
    
    def _check_file_changes(self) -> bool:
        """检查文件是否变化
        
        Returns:
            是否有变化
        """
        current_hash = self._calculate_directory_hash()
        
        if current_hash != self.last_hash:
            self.last_hash = current_hash
            self._rebuild_file_index()
            self._save_context()
            return True
        return False
    
    def _rebuild_file_index(self) -> None:
        """重建文件索引"""
        files = self._get_project_files()
        self.file_index = {}
        
        for file_path in files:
            try:
                relative_path = os.path.relpath(file_path, self.project_dir)
                file_stat = os.stat(file_path)
                
                # 获取文件扩展名
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # 获取文件内容摘要（前100个字符）
                content_preview = ""
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content_preview = f.read(100)
                except Exception:
                    pass
                
                self.file_index[relative_path] = {
                    "path": file_path,
                    "size": file_stat.st_size,
                    "modified": file_stat.st_mtime,
                    "extension": file_ext,
                    "preview": content_preview
                }
            except Exception:
                continue
    
    def get_project_summary(self) -> str:
        """获取项目摘要
        
        Returns:
            项目摘要字符串
        """
        if not self.file_index:
            return "项目为空或未找到文件"
        
        # 统计文件类型
        file_types = {}
        for file_info in self.file_index.values():
            ext = file_info["extension"]
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # 获取主要文件类型
        if file_types:
            main_type = max(file_types, key=file_types.get)
            type_count = file_types[main_type]
        else:
            main_type = "无"
            type_count = 0
        
        # 统计总文件数
        total_files = len(self.file_index)
        
        # 获取最近修改的文件
        sorted_files = sorted(
            self.file_index.values(),
            key=lambda x: x["modified"],
            reverse=True
        )
        recent_files = sorted_files[:5]
        
        # 构建摘要
        summary_parts = [
            f"项目包含 {total_files} 个文件",
            f"主要文件类型: {main_type} ({type_count} 个文件)",
            "\n最近修改的文件:"
        ]
        
        for file_info in recent_files:
            relative_path = os.path.relpath(file_info["path"], self.project_dir)
            summary_parts.append(f"  - {relative_path}")
        
        return "\n".join(summary_parts)
    
    def search_files(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索文件
        
        Args:
            query: 搜索查询
            limit: 返回结果限制
            
        Returns:
            匹配的文件列表
        """
        query_lower = query.lower()
        results = []
        
        for relative_path, file_info in self.file_index.items():
            # 在文件名中搜索
            if query_lower in relative_path.lower():
                results.append(file_info)
                if len(results) >= limit:
                    break
            
            # 在文件内容预览中搜索
            elif query_lower in file_info.get("preview", "").lower():
                results.append(file_info)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """获取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容或 None
        """
        # 转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.project_dir, file_path)
        
        # 检查文件是否在索引中
        relative_path = os.path.relpath(file_path, self.project_dir)
        if relative_path not in self.file_index:
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    
    def clear_context(self) -> None:
        """清空项目上下文"""
        self.context = {}
        self.file_index = {}
        self.last_hash = ""
        self._save_context()
