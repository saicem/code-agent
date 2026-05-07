# Code Agent

一个轻量级的代码代理工具，用于自主执行代码相关任务。

## 功能特点

- 🤖 **智能代码执行** - 支持多种工具调用，自动完成代码任务
- 📝 **会话管理** - 支持会话的创建、保存和加载
- 🧠 **记忆系统** - 持久化存储用户偏好和项目上下文
- 🔍 **文件操作** - 支持文件的读取、写入、搜索和修改
- 📊 **监控追踪** - 集成 OpenTelemetry 进行分布式追踪和日志记录
- 🔄 **自动压缩** - 智能压缩会话上下文，避免 token 超限

## 技术栈

- **语言**: Python 3.13+
- **依赖管理**: uv
- **API 客户端**: OpenAI Python SDK
- **依赖注入**: dependency-injector
- **配置管理**: pydantic-settings
- **监控**: OpenTelemetry
- **HTTP 客户端**: httpx

## 快速开始

### 安装依赖

```bash
uv sync
```

### 配置环境变量

创建 `.env` 文件：

```env
# API 配置
API_KEY=your-api-key-here
BASE_URL=https://api.example.com/v1  # 可选，默认使用 OpenAI
MODEL=gpt-4o-mini

# 存储配置（可选）
STORAGE_DIR=.memo
```

### 运行代理

```bash
python src/code_agent/main.py
```

或使用命令行参数：

```bash
python src/code_agent/main.py --model gpt-4o-mini --base-url https://api.example.com/v1
```

## 使用方法

运行后，代理会提示您输入任务描述：

```
任务: 帮我创建一个 Python 脚本，用于统计目录下的文件数量
```

代理会自动分析任务，调用相关工具，并返回结果。

## 项目结构

```
src/code_agent/
├── agent/                 # 代理核心模块
│   ├── app.py            # 应用入口
│   ├── engine.py         # 思考引擎（ReAct 循环）
│   ├── gate.py           # AI 网关
│   ├── memory.py         # 记忆服务
│   ├── session.py        # 会话类
│   ├── session_manager.py # 会话管理器
│   └── prompt.py         # 提示词模板
├── commands/              # 命令处理
│   ├── session.py        # 会话相关命令
│   └── system.py         # 系统命令
├── core/                  # 核心模块
│   ├── config.py         # 配置管理
│   ├── container.py      # 依赖注入容器
│   ├── exceptions.py     # 异常定义
│   ├── otlp.py           # OpenTelemetry 配置
│   └── state.py          # 全局状态
├── tools/                 # 工具模块
│   ├── bash_tool.py      # Bash 命令工具
│   ├── edit_tool.py      # 文件编辑工具
│   ├── glob_tool.py      # 文件匹配工具
│   ├── grep_tool.py      # 文本搜索工具
│   ├── read_tool.py      # 文件读取工具
│   ├── write_tool.py     # 文件写入工具
│   └── _manager.py       # 工具管理器
├── utils/                 # 工具函数
│   ├── output.py         # 输出格式化
│   └── path_spec.py      # 路径规格处理
├── __init__.py
└── main.py               # 主入口
```

## 开发指南

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 使用 `ty check` 进行类型检查
- 使用 `ruff format` 格式化代码
- 使用 `ruff check --fix` 修复代码问题

### 运行检查

```bash
# 类型检查
ty check

# 代码格式化
ruff format

# 代码规范检查
ruff check --fix
```

### 添加新工具

1. 在 `tools/` 目录下创建新工具文件
2. 使用 `@tool` 装饰器注册工具
3. 在 `tools/__init__.py` 中导出工具

