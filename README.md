# Code Agent

## 技术栈

- Python 3.13+
- uv

## 快速开始

### 安装依赖

```bash
uv sync
```

### 运行

```bash
python src/code_agent/main.py --model Qwen3.5
```

### 配置

环境变量：
- `API_KEY` - API 密钥
- `BASE_URL` - API 基础 URL（可选）
- `MODEL` - 模型名称

### TODO

上下文压缩
metric 支持
长期记忆
复杂任务简单压缩 tool 输出会导致任务处理效果差