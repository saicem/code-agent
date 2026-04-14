#!/usr/bin/env python3
"""
LlamaIndex RAG 模块（使用 ChromaDB 缓存）
"""

import os

from code_agent.project_context import ProjectContextManager
from code_agent.config import config
from typing import Any
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb


class RAGManager:
    """RAG 管理类（使用 LlamaIndex 和 ChromaDB 实现）"""

    def __init__(self, project_context: ProjectContextManager):
        """初始化 RAG 管理器

        Args:
            project_context: 项目上下文管理器
        """
        self.project_context = project_context
        self.project_dir = project_context.project_dir
        self.chroma_db_path = config.rag_chroma_db_path

        # 配置 LlamaIndex
        self._configure_llama_index()

        # 构建或加载索引
        self.index = self._build_or_load_index()

        # 创建检索器
        if self.index:
            self.retriever = self.index.as_retriever(
                similarity_top_k=config.rag_similarity_top_k
            )
        else:
            self.retriever = None

    def _configure_llama_index(self):
        """配置 LlamaIndex"""
        # 设置嵌入模型
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def _calculate_directory_hash(self) -> str:
        """计算项目目录的哈希值，用于检测文件变化

        Returns:
            目录哈希值
        """
        # 复用项目上下文的目录哈希计算
        return self.project_context.context.last_hash

    def _build_or_load_index(self):
        """构建或加载索引

        Returns:
            向量存储索引
        """
        try:
            # 确保 .memo 目录存在
            os.makedirs(".memo", exist_ok=True)

            # 计算当前目录哈希
            current_hash = self._calculate_directory_hash()

            # 检查是否需要更新索引
            index_hash_file = os.path.join(".memo", "rag_index_hash.txt")
            need_update = True

            if os.path.exists(index_hash_file):
                with open(index_hash_file, "r") as f:
                    stored_hash = f.read().strip()
                if stored_hash == current_hash:
                    need_update = False

            if need_update:
                print("检测到文件变化，重新构建 RAG 索引...")
                # 构建新索引
                index = self._build_index()
                if index:
                    # 保存当前哈希
                    with open(index_hash_file, "w") as f:
                        f.write(current_hash)
                return index
            else:
                print("使用缓存的 RAG 索引...")
                # 加载现有索引
                return self._load_index()
        except Exception as e:
            print(f"构建或加载索引失败: {e}")
            return None

    def _build_index(self):
        """构建文档索引

        Returns:
            向量存储索引
        """
        try:
            # 读取项目目录中的文件
            documents = SimpleDirectoryReader(
                input_dir=str(self.project_dir),
                recursive=True,
                exclude=[
                    ".git",
                    ".venv",
                    "__pycache__",
                    "node_modules",
                    ".vscode",
                    ".idea",
                    ".memo",
                    "test",
                    "**/*.egg-info",
                ],
            ).load_data()

            # 初始化 ChromaDB
            chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            chroma_collection = chroma_client.get_or_create_collection("code_agent")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # 构建索引
            index = VectorStoreIndex.from_documents(
                documents, storage_context=storage_context
            )
            return index
        except Exception as e:
            print(f"构建索引失败: {e}")
            return None

    def _load_index(self):
        """加载现有索引

        Returns:
            向量存储索引
        """
        try:
            # 初始化 ChromaDB
            chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            chroma_collection = chroma_client.get_or_create_collection("code_agent")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # 加载索引
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store, storage_context=storage_context
            )
            return index
        except Exception as e:
            print(f"加载索引失败: {e}")
            return None

    def retrieve_relevant_files(
        self, query: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """检索相关文件

        Args:
            query: 查询字符串
            limit: 返回文件数量限制

        Returns:
            相关文件列表
        """
        if not self.index:
            return []

        try:
            # 使用 LlamaIndex 检索相关文档
            if self.retriever:
                nodes = self.retriever.retrieve(query, top_k=limit)
            else:
                # 回退到原始搜索方法
                file_infos = self.project_context.search_files(query, limit)
                # 转换 FileInfo 对象为字典
                return [
                    {
                        "path": info.path,
                        "size": info.size,
                        "modified": info.modified,
                        "extension": info.extension,
                        "preview": info.preview,
                    }
                    for info in file_infos
                ]

            # 处理检索结果
            relevant_files = []
            seen_files = set()

            for node in nodes:
                file_path = node.metadata.get("file_path", "")
                if file_path and file_path not in seen_files:
                    seen_files.add(file_path)
                    relative_path = os.path.relpath(file_path, self.project_dir)

                    # 从项目上下文中获取文件信息
                    if relative_path in self.project_context.context.file_index:
                        file_info = self.project_context.context.file_index[
                            relative_path
                        ]
                        relevant_files.append(
                            {
                                "path": file_info.path,
                                "size": file_info.size,
                                "modified": file_info.modified,
                                "extension": file_info.extension,
                                "preview": file_info.preview,
                            }
                        )

            return relevant_files[:limit]
        except Exception as e:
            print(f"检索文件失败: {e}")
            # 回退到原始搜索方法
            file_infos = self.project_context.search_files(query, limit)
            # 转换 FileInfo 对象为字典
            return [
                {
                    "path": info.path,
                    "size": info.size,
                    "modified": info.modified,
                    "extension": info.extension,
                    "preview": info.preview,
                }
                for info in file_infos
            ]

    def get_file_context(self, file_path: str, max_lines: int = 50) -> str | None:
        """获取文件上下文

        Args:
            file_path: 文件路径
            max_lines: 最大行数

        Returns:
            文件上下文字符串或 None
        """
        return self.project_context.get_file_content(file_path)

    def build_retrieval_context(self, query: str) -> str:
        """构建检索上下文

        Args:
            query: 查询字符串

        Returns:
            检索上下文字符串
        """
        if not self.index:
            # 回退到原始方法
            return self._build_retrieval_context_fallback(query)

        try:
            # 使用 LlamaIndex 检索相关文档
            if self.retriever:
                nodes = self.retriever.retrieve(query, top_k=3)
            else:
                # 回退到原始方法
                return self._build_retrieval_context_fallback(query)

            if not nodes:
                return "未找到相关文件"

            # 构建上下文
            context_parts = ["相关文件内容:"]

            for i, node in enumerate(nodes, 1):
                file_path = node.metadata.get("file_path", "")
                if file_path:
                    relative_path = os.path.relpath(file_path, self.project_dir)
                    context_parts.append(f"\n{i}. {relative_path}")
                    context_parts.append("```")
                    context_parts.append(node.text[:2000])  # 限制文本长度
                    if len(node.text) > 2000:
                        context_parts.append("... (内容已截断)")
                    context_parts.append("```")

            return "\n".join(context_parts)
        except Exception as e:
            print(f"构建检索上下文失败: {e}")
            # 回退到原始方法
            return self._build_retrieval_context_fallback(query)

    def _build_retrieval_context_fallback(self, query: str) -> str:
        """构建检索上下文的回退方法

        Args:
            query: 查询字符串

        Returns:
            检索上下文字符串
        """
        # 检索相关文件
        relevant_files = self.project_context.search_files(query, 3)

        if not relevant_files:
            return "未找到相关文件"

        # 构建上下文
        context_parts = ["相关文件内容:"]

        for i, file_info in enumerate(relevant_files, 1):
            relative_path = os.path.relpath(file_info.path, self.project_dir)
            context_parts.append(f"\n{i}. {relative_path}")

            # 获取文件内容
            file_content = self.get_file_context(relative_path)
            if file_content:
                context_parts.append("```")
                context_parts.append(file_content)
                context_parts.append("```")
            else:
                context_parts.append("无法读取文件内容")

        return "\n".join(context_parts)

    def search_code_snippets(
        self, query: str, file_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """搜索代码片段

        Args:
            query: 查询字符串
            file_types: 文件类型过滤（如 ['.py', '.js']）

        Returns:
            代码片段列表
        """
        # 回退到原始方法
        snippets = []

        # 获取所有文件
        for relative_path, file_info in self.project_context.context.file_index.items():
            # 过滤文件类型
            if file_types:
                ext = file_info.extension
                if ext not in file_types:
                    continue

            # 读取文件内容
            content = self.project_context.get_file_content(relative_path)
            if content is None:
                continue

            # 搜索匹配的行
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    snippets.append(
                        {
                            "file": relative_path,
                            "line": line_num,
                            "content": line.strip(),
                            "context": self._get_line_context(lines, line_num),
                        }
                    )

        return snippets

    def _get_line_context(
        self, lines: list[str], line_num: int, context_lines: int = 2
    ) -> list[str]:
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
