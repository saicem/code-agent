#!/usr/bin/env python3
"""
记忆管理服务类
合并用户上下文和项目上下文为"记忆"，存储在 .memo/ 目录下

**核心要求**：所有文档必须写入文件，确保持久化存储
- 记忆文件：.memo/auto_memory.md
"""

import logging
import os

from code_agent.core.config import Config
from code_agent.core.state import tracer
from code_agent.utils import print_system_output
from code_agent.utils.path_spec import DEFAULT_IGNORE_SPEC, get_pathspec_from_gitignore

_logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理服务"""

    def __init__(self, config: Config) -> None:
        self.auto_memory = config.storage.auto_memory
        self._file_ignore_spec = get_pathspec_from_gitignore(".gitignore") or DEFAULT_IGNORE_SPEC

    @tracer.start_as_current_span("save_compressed_data")
    def save_compressed_data(self, auto_memory: str) -> None:
        """将用户偏好和项目情况持久化到文件"""
        if auto_memory:
            try:
                with open(self.auto_memory, "w", encoding="utf-8") as f:
                    f.write(auto_memory)
                _logger.debug(f"记忆已保存到: {self.auto_memory}")
            except Exception as e:
                _logger.error(f"保存记忆失败: {e}", exc_info=True)

    @tracer.start_as_current_span("load_memory")
    def load_memory(self) -> str:
        """加载记忆文件，读取 project.md 和 preference.md 并以 XML 标签包含"""
        _logger.info("开始加载记忆文件")
        print_system_output("正在加载记忆文件...", "info")

        auto_memory_content = ""
        if os.path.exists(self.auto_memory):
            try:
                with open(self.auto_memory, "r", encoding="utf-8") as f:
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

        return memory
