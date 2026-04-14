#!/usr/bin/env python3
"""
LlamaIndex RAG 模块（使用 ChromaDB 缓存）
"""

import os
import hashlib
import json

from code_agent.contexts import ProjectContextManager
from code_agent.config import config
from code_agent.file_ignore import FileIgnoreManager
from typing import Any
from llama_index.core import (
    VectorStoreIndex,
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

        # 初始化文件忽略管理器
        self.ignore_manager = FileIgnoreManager(str(self.project_dir))

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

    def _build_or_load_index(self):
        """构建或加载索引

        Returns:
            向量存储索引
        """
        try:
            # 确保 .memo 目录存在
            os.makedirs(".memo", exist_ok=True)

            # 加载文件哈希记录
            file_hash_file = os.path.join(".memo", "rag_file_hashes.json")
            file_hashes = self._load_file_hashes(file_hash_file)

            # 获取当前项目中的所有文件及其哈希
            current_files = self._get_project_files_with_hashes()

            # 检查是否有文件变化
            changed_files = self._get_changed_files(file_hashes, current_files)

            if changed_files:
                print(f"检测到 {len(changed_files)} 个文件变化，更新 RAG 索引...")
                # 增量更新索引
                index = self._update_index(changed_files, file_hashes, current_files)
                if index:
                    # 保存文件哈希记录
                    self._save_file_hashes(file_hash_file, current_files)
                return index
            else:
                print("使用缓存的 RAG 索引...")
                # 加载现有索引
                return self._load_index()
        except Exception as e:
            print(f"构建或加载索引失败: {e}")
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

    def _load_file_hashes(self, file_hash_file: str) -> dict[str, str]:
        """加载文件哈希记录

        Args:
            file_hash_file: 文件哈希记录文件路径

        Returns:
            文件哈希字典
        """
        if os.path.exists(file_hash_file):
            try:
                with open(file_hash_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_file_hashes(self, file_hash_file: str, file_hashes: dict[str, str]):
        """保存文件哈希记录

        Args:
            file_hash_file: 文件哈希记录文件路径
            file_hashes: 文件哈希字典
        """
        try:
            with open(file_hash_file, "w", encoding="utf-8") as f:
                json.dump(file_hashes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件哈希记录失败: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件哈希值
        """
        try:
            hash_obj = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""

    def _get_project_files_with_hashes(self) -> dict[str, str]:
        """获取项目中的所有文件及其哈希

        Returns:
            文件哈希字典
        """
        file_hashes = {}

        for root, dirs, files in os.walk(self.project_dir):
            # 过滤忽略的目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in [
                    ".git",
                    ".venv",
                    "__pycache__",
                    "node_modules",
                    ".vscode",
                    ".idea",
                    ".memo",
                    "test",
                ]
            ]

            for filename in files:
                file_path = os.path.join(root, filename)
                if self.ignore_manager.is_ignored(file_path):
                    continue

                if os.path.isfile(file_path):
                    try:
                        file_hash = self._calculate_file_hash(file_path)
                        relative_path = os.path.relpath(file_path, self.project_dir)
                        file_hashes[relative_path] = file_hash
                    except Exception:
                        continue

        return file_hashes

    def _get_changed_files(
        self, old_hashes: dict[str, str], new_hashes: dict[str, str]
    ) -> list[str]:
        """获取有变化的文件

        Args:
            old_hashes: 旧的文件哈希字典
            new_hashes: 新的文件哈希字典

        Returns:
            有变化的文件列表
        """
        changed_files = []

        # 检查新增或修改的文件
        for file_path, new_hash in new_hashes.items():
            old_hash = old_hashes.get(file_path)
            if old_hash != new_hash:
                changed_files.append(file_path)

        # 检查删除的文件（从索引中移除）
        for file_path in old_hashes:
            if file_path not in new_hashes:
                changed_files.append(f"DELETED:{file_path}")

        return changed_files

    def _update_index(
        self,
        changed_files: list[str],
        old_hashes: dict[str, str],
        new_hashes: dict[str, str],
    ):
        """增量更新索引

        Args:
            changed_files: 有变化的文件列表
            old_hashes: 旧的文件哈希字典
            new_hashes: 新的文件哈希字典

        Returns:
            向量存储索引
        """
        try:
            # 初始化 ChromaDB
            chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            chroma_collection = chroma_client.get_or_create_collection("code_agent")

            # 处理每个变化的文件
            for file_path in changed_files:
                if file_path.startswith("DELETED:"):
                    # 删除文件
                    relative_path = file_path[8:]  # 移除 "DELETED:" 前缀
                    print(f"  删除索引: {relative_path}")
                    try:
                        # 删除对应的文档
                        chroma_collection.delete(ids=[relative_path])
                    except Exception as e:
                        print(f"  删除索引失败: {e}")
                else:
                    # 更新文件
                    print(f"  更新索引: {file_path}")
                    try:
                        full_path = os.path.join(self.project_dir, file_path)
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # 删除旧的文档
                        try:
                            chroma_collection.delete(ids=[file_path])
                        except Exception:
                            pass

                        # 添加新文档
                        chroma_collection.add(
                            documents=[content],
                            ids=[file_path],
                            metadatas=[
                                {
                                    "file_path": file_path,
                                    "file_name": os.path.basename(file_path),
                                }
                            ],
                        )
                    except Exception as e:
                        print(f"  更新索引失败: {e}")

            # 重新加载索引
            return self._load_index()
        except Exception as e:
            print(f"更新索引失败: {e}")
            return None

    def _find_file_info(self, relative_path: str) -> dict | None:
        """在项目上下文中查找文件信息

        Args:
            relative_path: 相对路径

        Returns:
            文件信息字典或 None
        """
        file_structure = self.project_context.context.get("file_structure", {})
        assert isinstance(file_structure, dict), "file_structure should be a dict"
        files = file_structure.get("files", [])
        assert isinstance(files, list), "files should be a list"

        for file_info in files:
            if file_info.get("path") == relative_path:
                return file_info

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
                    file_info = self._find_file_info(relative_path)
                    if file_info:
                        relevant_files.append(
                            {
                                "path": file_info.get("path", relative_path),
                                "size": file_info.get("size", 0),
                                "modified": file_info.get("modified", 0),
                                "extension": file_info.get("extension", ""),
                                "preview": "",
                            }
                        )

            return relevant_files[:limit]
        except Exception as e:
            print(f"检索文件失败: {e}")
            # 回退到原始搜索方法
            file_infos = self.project_context.search_files(query, limit)
            return file_infos

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
            relative_path = file_info.get("path", "")
            context_parts.append(f"\n{i}. {relative_path}")

            # 获取文件内容
            file_content = self.project_context.get_file_content(relative_path)
            if file_content:
                context_parts.append("```")
                context_parts.append(file_content[:2000])  # 限制长度
                if len(file_content) > 2000:
                    context_parts.append("... (内容已截断)")
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
        file_structure = self.project_context.context.get("file_structure", {})
        assert isinstance(file_structure, dict), "file_structure should be a dict"
        files = file_structure.get("files", [])
        assert isinstance(files, list), "files should be a list"

        for file_info in files:
            relative_path = file_info.get("path", "")
            ext = file_info.get("extension", "")

            # 过滤文件类型
            if file_types and ext not in file_types:
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
