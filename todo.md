# Code Agent 重构任务清单

## 优先级说明
- **P0** - 紧急修复，核心功能受影响
- **P1** - 重要改进，影响可维护性和稳定性
- **P2** - 架构优化，提升扩展性
- **P3** - 代码质量改进

---

## P0 - 紧急修复

### 1. MemoryManager 重复赋值问题
**文件**: `src/code_agent/agent/memory.py`
**问题**: `__init__` 中 `self.file_update` 和 `self.auto_memory` 都赋值为 `config.storage.auto_memory`，导致文件变更检测功能失效
**修复**: 将 `self.file_update` 改为 `config.storage.file_update`

### 2. Session.set_system_prompt 封装缺陷
**文件**: `src/code_agent/agent/session.py`
**问题**: `set_system_prompt` 设置的是实例属性 `self.system_prompt`，而非 `self.data.system_prompt`，导致系统提示词无法正确保存
**修复**: 修改为 `self.data.system_prompt = content`，并同步更新 `messages_for_model()` 方法

---

## P1 - 重要改进

### 3. 容器配置提前求值问题
**文件**: `src/code_agent/core/container.py`
**问题**: `session_manager` 定义时直接调用 `config().storage.sessions_dir`，导致配置在容器定义时就被初始化，无法延迟加载
**修复**: 使用 `providers.Callable` 延迟求值

### 4. 工具参数解析缺失
**文件**: `src/code_agent/tools/__init__.py`、`src/code_agent/tools/_manager.py`
**问题**: 工具调用时直接将 JSON 字符串传递给工具函数，缺乏参数验证
**修复**: 在 `_manager.py` 中新增 `invoke_tool` 函数，统一解析和验证参数

---

## P2 - 架构优化

### 5. 状态管理封装不足
**文件**: `src/code_agent/core/state.py`
**问题**: `current_session` 使用原始 `contextvars.ContextVar`，缺乏封装和类型安全
**修复**: 创建 `SessionContext` 类封装会话状态管理

### 6. 异常体系不完善
**文件**: `src/code_agent/core/exceptions.py`
**问题**: 仅定义了 `SystemException`，缺乏分层异常体系
**修复**: 建立 `CodeAgentError` 基类及子类体系（`ToolError`、`ConfigurationError`、`SessionError`）

---

## P3 - 代码质量改进

### 7. 日志命名规范问题
**文件**: `src/code_agent/agent/memory.py`
**问题**: 使用 `logging.getLogger(__file__)` 而非 `logging.getLogger(__name__)`
**修复**: 改为 `logging.getLogger(__name__)`

### 8. 执行策略设计优化
**文件**: `src/code_agent/agent/engine.py`
**问题**: `plan_and_execute` 方法无实际规划逻辑，扩展性受限
**修复**: 引入 `ExecutionStrategy` 接口和多种策略实现

---

## 检查清单

- [x] 所有修改通过 `ty check` 类型检查
- [x] 所有修改通过 `ruff format` 格式化
- [x] 所有修改通过 `ruff check --fix` 代码检查
- [ ] 添加必要的单元测试
- [ ] 更新相关文档

---

## 完成状态

| 序号 | 任务 | 状态 | 负责人 | 截止日期 |
|------|------|------|--------|----------|
| 1 | MemoryManager 重复赋值 | ✅ 已完成 | - | - |
| 2 | Session.set_system_prompt | ✅ 已完成 | - | - |
| 3 | 容器配置提前求值 | ✅ 已完成 | - | - |
| 4 | 工具参数解析缺失 | ✅ 已完成 | - | - |
| 5 | 状态管理封装 | ✅ 已完成 | - | - |
| 6 | 异常体系完善 | ✅ 已完成 | - | - |
| 7 | 日志命名规范 | ✅ 已完成 | - | - |
| 8 | 执行策略设计 | ⏳ 待处理 | - | - |
