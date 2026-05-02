# Code Agent 项目

## 技术栈
- Language: Python 3.13+
- Dependency Manager: uv

## 约定
- **dataclass**：优先使用 `@dataclass` 定义数据结构
- **统一配置**：集中管理配置参数
- **类型注解**：为函数添加类型注解，优先使用内置类型（如 `list dict str set`），优先使用 `X | None` 而不是 `Optional[X]`，优先使用 `X | Y` 而不是 `Union[X, Y]`
- **类型检查**：每次变更后运行 `ty check` 和 `ruff format`
- **模块化设计**：当单个文件内容过多功能过于复杂时，尝试将其重构划分为多个模块
- **不要使用 kwargs**：在函数定义中避免使用 kwargs，因为 kwargs 会导致类型检查困难和代码可读性下降
- **命名遵循 PEP 8**：所有代码都必须符合 PEP 8 规范，包括变量名、函数名、类名等
