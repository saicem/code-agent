# Code Agent 项目

## 技术栈
- Language: Python 3.13+
- Dependency Manager: uv

## 约定
- Python 为 3.13+ 以上版本，优先使用新版本写法
- 在函数定义中避免使用 kwargs，使用具体类型，复杂参数使用 `@dataclass` 定义数据结构
- 集中管理配置参数，通过 `code_agent.core.config` 模块提供定义和访问
- 函数添加类型注解，优先使用内置类型（如 `list dict str set`），优先使用 `X | None` 而不是 `Optional[X]`，优先使用 `X | Y` 而不是 `Union[X, Y]`
- 每次代码变更后执行检查 `ty check` `ruff format` `ruff check --fix`
- 模块化设计：当单个文件内容过多功能过于复杂时，尝试将其重构划分为多个模块
- 命名遵循 PEP 8：所有代码都必须符合 PEP 8 规范，包括变量名、函数名、类名等
- 需要记录 log 和 trace