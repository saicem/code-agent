#!/usr/bin/env python3
"""
记忆管理模块（函数式）
合并用户上下文和项目上下文为"记忆"，存储在 .memo/ 目录下
支持文件变更检测和文档更新

**核心要求**：所有文档必须写入文件，确保持久化存储
- 记忆文件：.memo/auto_memory.md
"""

import json
import os
from datetime import datetime
from typing import List, Tuple

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from code_agent.core.config import Config
from code_agent.core.container import Container
from code_agent.monitoring import get_logger, get_tracer
from code_agent.utils import print_system_output
from code_agent.utils.path_spec import DEFAULT_IGNORE_SPEC, get_pathspec_from_gitignore

_tracer = get_tracer(__file__)
_logger = get_logger(__file__)


class FileUpdateData(BaseModel):
    """文件更新记录数据结构"""

    files: dict[str, float] = {}  # 文件路径 -> 修改时间戳
    last_check: str = datetime.now().isoformat()  # 上次检查时间（ISO格式）


_file_ignore_spec = get_pathspec_from_gitignore(".gitignore") or DEFAULT_IGNORE_SPEC


@inject
def save_compressed_data(auto_memory: str, config: Config = Provide[Container.config]) -> None:
    """将用户偏好和项目情况持久化到文件"""

    if auto_memory:
        try:
            with open(config.storage.auto_memory, "w", encoding="utf-8") as f:
                f.write(auto_memory)
            _logger.debug(f"记忆已保存到: {config.storage.auto_memory}")
        except Exception as e:
            _logger.error(f"保存记忆失败: {e}", exc_info=True)


@_tracer.start_as_current_span("load_memory")
@inject
def load_memory(config: Config = Provide[Container.config]) -> str:
    """加载记忆文件，读取 project.md 和 preference.md 并以 XML 标签包含"""
    _logger.info("开始加载记忆文件")
    print_system_output("正在加载记忆文件...", "info")

    # 读取记忆文件
    auto_memory_content = ""
    if os.path.exists(config.storage.auto_memory):
        try:
            with open(config.storage.auto_memory, "r", encoding="utf-8") as f:
                auto_memory_content = f.read()
            _logger.debug(f"成功读取记忆文件，内容长度: {len(auto_memory_content)}")
        except Exception as e:
            _logger.error(f"读取 preference.md 失败: {e}")
            print_system_output(f"读取 preference.md 失败: {e}", "error")
    else:
        _logger.debug("记忆文件 不存在")

    memory = f"""
<auto_memory>
{auto_memory_content}
</auto_memory>

"""

    _logger.info(f"记忆文件加载完成，总长度: {len(memory)}")
    print_system_output("记忆文件加载完成", "success")

    # 以 XML 标签格式组合内容
    return memory


@inject
def _load_file_updates(config: Config = Provide[Container.config]) -> FileUpdateData | None:
    """加载文件更新记录"""
    _logger.debug(f"尝试加载文件更新记录: {config.storage.file_update}")
    if os.path.exists(config.storage.file_update):
        try:
            with open(config.storage.file_update, "r", encoding="utf-8") as f:
                data = json.load(f)
                result = FileUpdateData(**data)
                _logger.debug(f"成功加载文件更新记录，包含 {len(result.files)} 个文件")
                return result
        except Exception as e:
            _logger.error(f"加载文件更新记录失败: {e}")
            print_system_output(f"加载文件更新记录失败: {e}", "error")
    else:
        _logger.debug("文件更新记录不存在")
    return None


@inject
def _save_file_updates(
    file_updates: FileUpdateData, config: Config = Provide[Container.config]
) -> None:
    """保存文件更新记录"""
    file_updates.last_check = datetime.now().isoformat()
    try:
        with open(config.storage.file_update, "w", encoding="utf-8") as f:
            json.dump(file_updates.model_dump(), f, indent=2, ensure_ascii=False)
        _logger.debug(f"成功保存文件更新记录，包含 {len(file_updates.files)} 个文件")
    except Exception as e:
        _logger.error(f"保存文件更新记录失败: {e}")
        print_system_output(f"保存文件更新记录失败: {e}", "error")


def _detect_file_changes(
    current_files: dict[str, float],
    last_file_update_data: FileUpdateData | None,
) -> Tuple[List[str], List[str], List[str]]:
    """
    检测文件变更

    Args:
        current_files: 当前文件及其修改时间戳
        last_file_update_data: 上次记录的文件更新数据

    Returns:
        (新增文件列表, 更新文件列表, 删除文件列表)
    """
    _logger.debug(f"开始检测文件变更，当前文件数: {len(current_files)}")

    added_files: List[str] = []
    updated_files: List[str] = []
    deleted_files: List[str] = []

    if last_file_update_data is None:
        added_files = list(current_files.keys())
        _logger.info(f"首次检测，所有 {len(added_files)} 个文件标记为新增")
        print_system_output(f"首次检测，发现 {len(added_files)} 个文件", "info")
    else:
        _logger.debug(f"上次记录的文件数: {len(last_file_update_data.files)}")
        # 遍历所有文件，判断是否新增、更新、删除
        for f, mtime in current_files.items():
            if f not in last_file_update_data.files:
                added_files.append(f)
            elif mtime != last_file_update_data.files[f]:
                updated_files.append(f)
        for f in last_file_update_data.files:
            if f not in current_files:
                deleted_files.append(f)

        _logger.info(
            f"文件变更检测完成: +{len(added_files)}新增, ~{len(updated_files)}更新, -{len(deleted_files)}删除"
        )
        if added_files or updated_files or deleted_files:
            print_system_output(
                f"检测到文件变更: +{len(added_files)}新增, ~{len(updated_files)}更新, -{len(deleted_files)}删除",
                "info",
            )
        else:
            _logger.debug("未检测到文件变更")

    return added_files, updated_files, deleted_files
