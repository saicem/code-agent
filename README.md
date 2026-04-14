# Code Agent

智能交互式命令行代码生成代理。

## 快速开始

### 前提条件
- **Ollama**：安装并运行 Ollama，下载模型（如 Qwen3.5）
- **百炼**：注册阿里云账号，获取 API key，设置环境变量 `DASHSCOPE_API_KEY`

### 安装运行
```bash
uv sync
python src/code_agent/main.py --platform ollama --model Qwen3.5
```

## 核心特性

- **三层上下文**：用户、项目、会话上下文管理
- **RAG 检索**：LlamaIndex + ChromaDB 实现代码检索
- **智能修改**：解析代码块并应用到目标文件

详细扩展建议见 [TODO.md](TODO.md)
