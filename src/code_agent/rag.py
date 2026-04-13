#!/usr/bin/env python3
"""
基础 RAG 模块
"""

import os
import re
from typing import List, Dict, Any, Optional
from code_agent.project_context import ProjectContextManager


class RAGManager:
    """RAG 管理类"""
    
    def __init__(self, project_context: ProjectContextManager):
        """初始化 RAG 管理器
        
        Args:
            project_context: 项目上下文管理器
        """
        self.project_context = project_context
    
    def retrieve_relevant_files(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """检索相关文件
        
        Args:
            query: 查询字符串
            limit: 返回文件数量限制
            
        Returns:
            相关文件列表
        """
        # 从项目上下文中搜索文件
        relevant_files = self.project_context.search_files(query, limit)
        
        # 如果搜索结果不足，尝试从文件名中匹配
        if len(relevant_files) < limit:
            # 提取查询中的关键词
            keywords = self._extract_keywords(query)
            
            # 搜索包含关键词的文件
            for keyword in keywords:
                if len(relevant_files) >= limit:
                    break
                
                keyword_files = self.project_context.search_files(keyword, limit - len(relevant_files))
                for file_info in keyword_files:
                    if file_info not in relevant_files:
                        relevant_files.append(file_info)
        
        return relevant_files[:limit]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词
        
        Args:
            query: 查询字符串
            
        Returns:
            关键词列表
        """
        # 移除常见的停用词
        stop_words = {"的", "了", "是", "在", "有", "和", "与", "或", "但", "不", "这", "那", "我", "你", "他", "她", "它", "们", "个", "种", "类", "样", "样", "样"}
        
        # 使用正则表达式提取中文和英文单词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query)
        
        # 过滤停用词
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def get_file_context(self, file_path: str, max_lines: int = 50) -> Optional[str]:
        """获取文件上下文
        
        Args:
            file_path: 文件路径
            max_lines: 最大行数
            
        Returns:
            文件上下文字符串或 None
        """
        content = self.project_context.get_file_content(file_path)
        
        if content is None:
            return None
        
        # 按行分割
        lines = content.split('\n')
        
        # 限制行数
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append("... (内容已截断)")
        
        return '\n'.join(lines)
    
    def build_retrieval_context(self, query: str) -> str:
        """构建检索上下文
        
        Args:
            query: 查询字符串
            
        Returns:
            检索上下文字符串
        """
        # 检索相关文件
        relevant_files = self.retrieve_relevant_files(query)
        
        if not relevant_files:
            return "未找到相关文件"
        
        # 构建上下文
        context_parts = ["相关文件内容:"]
        
        for i, file_info in enumerate(relevant_files, 1):
            relative_path = os.path.relpath(file_info["path"], self.project_context.project_dir)
            context_parts.append(f"\n{i}. {relative_path}")
            
            # 获取文件内容
            file_content = self.get_file_context(relative_path)
            if file_content:
                context_parts.append(f"```")
                context_parts.append(file_content)
                context_parts.append(f"```")
            else:
                context_parts.append("无法读取文件内容")
        
        return '\n'.join(context_parts)
    
    def search_code_snippets(self, query: str, file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """搜索代码片段
        
        Args:
            query: 查询字符串
            file_types: 文件类型过滤（如 ['.py', '.js']）
            
        Returns:
            代码片段列表
        """
        snippets = []
        
        # 获取所有文件
        for relative_path, file_info in self.project_context.file_index.items():
            # 过滤文件类型
            if file_types:
                ext = file_info["extension"]
                if ext not in file_types:
                    continue
            
            # 读取文件内容
            content = self.project_context.get_file_content(relative_path)
            if content is None:
                continue
            
            # 搜索匹配的行
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    snippets.append({
                        "file": relative_path,
                        "line": line_num,
                        "content": line.strip(),
                        "context": self._get_line_context(lines, line_num)
                    })
        
        return snippets
    
    def _get_line_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> List[str]:
        """获取行上下文
        
        Args:
            lines: 所有行
            line_num: 当前行号
            context_lines: 上下文行数
            
        Returns:
            上下文行列表
        """
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        return lines[start:end]