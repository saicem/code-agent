# Code Agent

一个智能的交互式命令行代码生成代理，具有上下文感知、RAG 检索和自动代码修改应用功能。

## 技术栈

- Python 3.11+
- uv (Python 包管理器)
- requests
- dashscope (用于百炼模型)

## 核心特性

### 1. 三层上下文管理
- **用户上下文**：从历史对话中总结用户偏好和模式，持久化存储
- **项目上下文**：自动扫描目录结构，建立文件索引，检测文件变化
- **会话上下文**：管理对话历史，自动压缩长上下文

### 2. RAG 检索增强
- 从任务描述中提取关键词
- 搜索相关文件并读取内容
- 将文件内容作为上下文提供给模型

### 3. 智能代码修改应用
- 解析代码块和确定目标文件
- 支持创建、更新、追加、删除操作
- 安全应用模式，可预览修改

## 快速开始

### 前提条件
- **Ollama**：安装并运行 Ollama，下载模型（如 Qwen3.5）
- **百炼模型**：注册阿里云账号，获取 API key，设置环境变量 `DASHSCOPE_API_KEY`

### 安装依赖
```bash
uv sync
```

### 运行示例
```bash
# 使用 Ollama
python src/code_agent/main.py --platform ollama --model Qwen3.5

# 使用百炼
python src/code_agent/main.py --platform bailian --model qwen3.5-max

# 指定项目目录
python src/code_agent/main.py --platform ollama --model Qwen3.5 --project-dir /path/to/project

# 应用代码修改
python src/code_agent/main.py --platform ollama --model Qwen3.5 --apply-changes

# 将输出写入文件
python src/code_agent/main.py --platform ollama --model Qwen3.5 --output output.txt
```

## 项目结构

```
code-agent/
├── .memo/               # 存储上下文数据
├── src/code_agent/      # 主源码目录
│   ├── agents/          # 不同平台的 Agent 实现
│   ├── agent.py         # Agent 工厂类
│   ├── code_modifier.py # 代码修改应用模块
│   ├── error_handling.py # 错误处理模块
│   ├── main.py          # 主入口文件
│   ├── project_context.py # 项目上下文管理
│   ├── rag.py           # RAG 检索模块
│   ├── security.py      # 安全管理模块
│   ├── session_context.py # 会话上下文管理
│   └── user_context.py  # 用户上下文管理
├── test/                # 测试文件目录
├── pyproject.toml       # 项目配置文件
└── README.md            # 项目说明文档
```

## 命令行指令

- **直接输入**：任务描述或代码修改请求
- **/quit**：退出程序
- **/about**：显示当前版本、平台、模型等信息
- **/help**：查看可用指令

## 注意事项
- 确保 Ollama 服务正在运行（默认端口 11434）
- 首次运行时会在 `.memo` 目录中创建必要的文件
- 错误信息会记录到 `agent.log` 文件
- 使用 `--apply-changes` 参数时要小心，会实际修改文件
- 仅用于开发和测试，不要在生产环境中使用

## 项目偏好

- **使用现代 typing**：优先使用 Python 3.11+ 的内置 typing 类型（如 `list[dict[str, any]]`），而不是从 `typing` 模块导入类型（如 `List[Dict[str, Any]]`）
- **使用 dataclass**：尽量创建 `@dataclass` 类型来定义数据结构，而不是使用字典，以提高类型安全性和代码可读性
- **统一配置管理**：使用集中的配置管理模块，将分散的配置参数统一管理
- **模块化设计**：保持代码的模块化和清晰的职责分离
- **类型注解**：为函数参数和返回值添加类型注解，提高代码的可维护性和可读性

## 扩展建议

详细的扩展建议和待办事项请查看 [TODO.md](TODO.md) 文件。