# Code Agent 项目

## 技术栈
- Language: Python 3.11+
- Dependency Manager: uv
- Model API: 百炼 OpenAI 兼容模式 (API_KEY)
- Tools: WriteTool, ReadTool, SearchTool
- RAG: LlamaIndex + ChromaDB

## 约定
- **dataclass**：优先使用 `@dataclass` 定义数据结构
- **统一配置**：集中管理配置参数
- **类型注解**：为函数添加类型注解
- **现代 typing**：尽量使用内置类型（如 `list[dict[str, Any]]`）不要引用 `typing`，除非没有对应的内置类型，如 `Any`
- **谨慎 Any**：尽量减少 `Any` 使用
- **类型策略**：优先推导确定类型，其次断言，最后才用 Any
- **类型检查**：每次变更后运行 `ty check`
- **代码格式化**：修改文件后使用 `ruff format`
- **模块化设计**：当单个文件内容过多功能过于复杂时，尝试将其重构划分为多个模块
- **文件结构**：当文件中有多个相似模块时，尝试重新组织文件结构以使项目更加清晰
- **不要使用 kwargs**：在函数定义中避免使用 kwargs，因为 kwargs 会导致类型检查困难和代码可读性下降

## 命令
- `ty check`: 类型检查
- `ruff format <file>`: 代码格式化
- `uv run dev --model <model>`: 运行 Code Agent
