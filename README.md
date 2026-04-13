# Code Agent

一个智能的交互式命令行代码生成代理，具有上下文感知、RAG 检索和自动代码修改应用功能。

## 技术栈

- Python 3.11+
- uv (Python 包管理器)
- requests
- dashscope (用于百炼模型)

## 核心特性

### 1. 三层上下文管理

Code Agent 在启动时会加载三个层次的上下文信息：

#### 1.1 用户上下文
- 从历史对话中总结用户偏好和模式
- 自动检测用户偏好的编程语言和任务类型
- 持久化存储用户偏好信息
- 随着对话不断更新和优化用户画像

#### 1.2 项目上下文
- 启动时自动扫描当前目录的文件结构
- 建立文件索引，记录文件路径、大小、修改时间等信息
- 通过哈希值检测文件变化，自动更新索引
- 提供项目摘要，包括文件类型统计和最近修改的文件

#### 1.3 会话上下文
- 管理当前会话的对话历史
- 当上下文过长时自动压缩旧对话为摘要
- 保留最近的完整对话内容
- 支持持久化存储会话历史

### 2. RAG 检索增强

当用户发出指令后，系统会：
- 从任务描述中提取关键词
- 在项目文件索引中搜索相关文件
- 读取相关文件的内容
- 将文件内容作为上下文提供给模型
- 支持代码片段搜索和上下文提取

### 3. 智能代码修改应用

系统通过规定并解析大模型的输出来决定代码修改：

#### 3.1 代码块解析
- 识别 ```language 格式的代码块
- 支持缩进格式的代码识别
- 提取代码内容和语言类型

#### 3.2 目标文件确定
- 从任务描述中提取文件名
- 根据代码语言自动添加扩展名
- 如果没有明确文件名，生成临时文件名

#### 3.3 操作类型识别
- 创建：新建文件
- 更新：修改现有文件
- 追加：在文件末尾添加内容
- 删除：删除文件

#### 3.4 安全应用
- 支持试运行模式（--apply-changes 参数控制）
- 显示将要修改的文件列表
- 应用后显示详细的修改摘要
- 记录所有修改操作

## 快速开始

### 1. 前提条件

#### 使用 Ollama (默认)
- 安装 Python 3.11+
- 安装 uv：`pip install uv`
- 安装并运行 Ollama：[https://ollama.com/download](https://ollama.com/download)
- 下载模型：`ollama pull Qwen3.5`

#### 使用百炼模型 API
- 安装 Python 3.11+
- 安装 uv：`pip install uv`
- 注册阿里云账号并开通百炼服务
- 获取 API key
- 设置环境变量：`export DASHSCOPE_API_KEY=your_api_key` (Linux/Mac) 或 `set DASHSCOPE_API_KEY=your_api_key` (Windows)

### 2. 安装依赖

```bash
uv sync
```

### 3. 运行

#### 基本用法
```bash
# 使用 Ollama
python src/code_agent/main.py --platform ollama --model Qwen3.5

# 使用百炼
# 先设置环境变量
export DASHSCOPE_API_KEY=your_api_key  # Linux/Mac
# 或
set DASHSCOPE_API_KEY=your_api_key  # Windows
# 然后运行
python src/code_agent/main.py --platform bailian --model qwen3.5-max
```

#### 指定项目目录
```bash
# 在特定项目目录中运行
python src/code_agent/main.py --platform ollama --model Qwen3.5 --project-dir /path/to/project
```

#### 应用代码修改
```bash
# 启用代码修改应用功能
python src/code_agent/main.py --platform ollama --model Qwen3.5 --apply-changes
```

#### 将输出写入文件
```bash
# 使用 Ollama 并将输出写入文件
python src/code_agent/main.py --platform ollama --model Qwen3.5 --output output.txt

# 使用百炼并将输出写入文件
python src/code_agent/main.py --platform bailian --model qwen3.5-max --output output.txt
```

## 项目结构

```
code-agent/
├── .memo/               # 存储记忆和上下文数据
│   ├── memory.json       # 记忆数据
│   ├── user_context.json # 用户上下文数据
│   ├── project_context.json # 项目上下文数据
│   └── session_context.json # 会话上下文数据
├── src/
│   └── code_agent/       # 主源码目录
│       ├── agents/       # 不同平台的 Agent 实现
│       ├── __init__.py
│       ├── agent.py      # Agent 工厂类
│       ├── code_modifier.py # 代码修改应用模块
│       ├── error_handling.py # 错误处理模块
│       ├── main.py       # 主入口文件
│       ├── memory.py     # 记忆管理模块
│       ├── project_context.py # 项目上下文管理模块
│       ├── rag.py        # RAG 检索模块
│       ├── security.py   # 安全管理模块
│       ├── session_context.py # 会话上下文管理模块
│       └── user_context.py # 用户上下文管理模块
├── test/                # 测试文件目录
│   └── test.py          # 测试文件
├── pyproject.toml       # 项目配置文件
└── README.md            # 项目说明文档
```

## 配置

- **模型选择**：通过命令行参数 `--model` 指定
- **平台选择**：通过命令行参数 `--platform` 指定
- **项目目录**：通过命令行参数 `--project-dir` 指定
- **输出文件**：通过命令行参数 `--output` 指定
- **应用修改**：通过命令行参数 `--apply-changes` 启用
- **存储目录**：所有记忆和上下文数据存储在 `.memo` 文件夹中
- **测试文件**：所有测试文件放在 `test` 文件夹中

## 注意事项

1. 确保 Ollama 服务正在运行（默认端口 11434）
2. 首次运行时会在 `.memo` 目录中创建必要的文件
3. 错误信息会记录到 `agent.log` 文件
4. 生成的代码可能需要手动验证和调整
5. 使用 `--apply-changes` 参数时要小心，会实际修改文件
6. 不要在生产环境中使用此代码，仅用于开发和测试

## 扩展建议

1. 添加更多模型支持
2. 实现更复杂的记忆管理策略
3. 添加代码执行和测试功能
4. 实现 Web 界面
5. 添加更多安全检查规则
6. 实现 Git 集成，自动提交修改
7. 添加代码审查功能
8. 实现更智能的 RAG 检索算法
9. 支持多项目上下文切换
10. 添加插件系统