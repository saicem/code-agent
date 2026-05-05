#!/usr/bin/env python3
"""
记忆管理模块（函数式）
合并用户上下文和项目上下文为"记忆"，存储在 .memo/ 目录下
支持文件变更检测和文档更新

**核心要求**：所有文档必须写入文件，确保持久化存储
- 用户偏好：.memo/preference.md
- 项目总览：.memo/project.md
- 模块文档：.memo/ref/module_xxx.md
"""

import json
import os
from datetime import datetime
from typing import List, Tuple

from pydantic import BaseModel

from code_agent.agent.engine import reasoning_acting
from code_agent.agent.prompt import MEMORY_CONTEXT_SYSTEM
from code_agent.agent.session import Session
from code_agent.agent.session_manager import get_session_manager
from code_agent.core.config import get_config
from code_agent.monitoring import get_logger, get_tracer
from code_agent.utils import print_system_output
from code_agent.utils.path_spec import DEFAULT_IGNORE_SPEC, get_pathspec_from_gitignore

_tracer = get_tracer(__name__)
_logger = get_logger(__name__)


class FileUpdateData(BaseModel):
    """文件更新记录数据结构"""

    files: dict[str, float] = {}  # 文件路径 -> 修改时间戳
    last_check: str = datetime.now().isoformat()  # 上次检查时间（ISO格式）


# 全局配置
_config = get_config()
_MEMO_DIR = _config.storage.storage_dir
_PROJECT_FILE = os.path.join(_MEMO_DIR, "project.md")
_PREFERENCE_FILE = os.path.join(_MEMO_DIR, "preference.md")
_FILE_UPDATE_FILE = os.path.join(_MEMO_DIR, "file_update.json")
_file_ignore_spec = get_pathspec_from_gitignore(".gitignore") or DEFAULT_IGNORE_SPEC
os.makedirs(os.path.join(_MEMO_DIR, "ref"), exist_ok=True)


@_tracer.start_as_current_span("load_memory")
def load_memory() -> str:
    """加载记忆文件，读取 project.md 和 preference.md 并以 XML 标签包含"""
    _logger.info("开始加载记忆文件")
    print_system_output("正在加载记忆文件...", "info")

    # 读取 preference.md
    preference_content = ""
    if os.path.exists(_PREFERENCE_FILE):
        try:
            with open(_PREFERENCE_FILE, "r", encoding="utf-8") as f:
                preference_content = f.read()
            _logger.debug(f"成功读取 preference.md，内容长度: {len(preference_content)}")
        except Exception as e:
            _logger.error(f"读取 preference.md 失败: {e}")
            print_system_output(f"读取 preference.md 失败: {e}", "error")
    else:
        _logger.debug("preference.md 不存在")

    # 读取 project.md
    project_content = ""
    if os.path.exists(_PROJECT_FILE):
        try:
            with open(_PROJECT_FILE, "r", encoding="utf-8") as f:
                project_content = f.read()
            _logger.debug(f"成功读取 project.md，内容长度: {len(project_content)}")
        except Exception as e:
            _logger.error(f"读取 project.md 失败: {e}")
            print_system_output(f"读取 project.md 失败: {e}", "error")
    else:
        _logger.debug("project.md 不存在")

    memory = f"""
<user_preferences>
{preference_content}
</user_preferences>
<project_info>
{project_content}
</project_info>
"""

    _logger.info(f"记忆文件加载完成，总长度: {len(memory)}")
    print_system_output("记忆文件加载完成", "success")

    # 以 XML 标签格式组合内容
    return memory


def _load_file_updates() -> FileUpdateData | None:
    """加载文件更新记录"""
    _logger.debug(f"尝试加载文件更新记录: {_FILE_UPDATE_FILE}")
    if os.path.exists(_FILE_UPDATE_FILE):
        try:
            with open(_FILE_UPDATE_FILE, "r", encoding="utf-8") as f:
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


def _save_file_updates(file_updates: FileUpdateData) -> None:
    """保存文件更新记录"""
    file_updates.last_check = datetime.now().isoformat()
    try:
        with open(_FILE_UPDATE_FILE, "w", encoding="utf-8") as f:
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


@_tracer.start_as_current_span("update_memory")
async def update_memory() -> None:
    """
    检测项目文件变更并更新文档
    """

    # 加载上次记录
    last_file_update_data = _load_file_updates()

    # 遍历获取目录下所有文件，过滤 _file_ignore_spec 中的文件，得到文件以及上次修改时间戳
    _logger.debug("开始扫描项目文件")
    file_updates: dict[str, float] = {}
    for f in _file_ignore_spec.match_tree_files(".", negate=True):
        file_updates[f] = os.path.getmtime(f)
    _logger.debug(f"扫描完成，共发现 {len(file_updates)} 个文件")

    session = Session()
    session.data.session_id = "memory_update" + session.data.session_id
    session.set_system_prompt(MEMORY_CONTEXT_SYSTEM)

    if last_file_update_data is None:
        _logger.info("首次运行，需要重建文档")
        print_system_output("首次运行，正在重建文档...", "info")
        session.add_user_message("你需要读取整个项目来重建文档")
        await reasoning_acting(session, "code")
        _logger.info("文档重建完成")
        print_system_output("文档重建完成", "success")

    else:
        # 检测文件变更
        added_files, updated_files, deleted_files = _detect_file_changes(
            file_updates, last_file_update_data
        )
        if len(added_files) > 0 or len(updated_files) > 0 or len(deleted_files) > 0:
            _logger.info("存在文件变更，需要更新文档")
            print_system_output("正在更新文档...", "info")
            session.add_user_message(
                f"以下文件发生了变化。新增: {added_files}, 更新: {updated_files}, 删除: {deleted_files}。根据文件变更修改文档。"
            )
            await reasoning_acting(session, "code")
            _logger.info("文档更新完成")
            print_system_output("文档更新完成", "success")
        else:
            _logger.info("未检测到文件变更，无需更新文档")
            print_system_output("未检测到文件变更", "info")

    # 保存文件更新记录
    get_session_manager().save_session(session)
    _save_file_updates(FileUpdateData(files=file_updates))
    _logger.info("记忆更新完成")
    print_system_output("记忆更新完成", "success")
