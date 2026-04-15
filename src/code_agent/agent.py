#!/usr/bin/env python3
"""
Code Agent 类
"""

from typing import Iterable, Any
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
    ChatCompletion,
)

import json
import re
from openai import OpenAI
from code_agent.error_handling import ErrorHandler, get_env_var
from code_agent.security import SecurityManager
from code_agent.config import config
from code_agent.tools.tool_manager import ToolManager


class CodeAgent:
    """Code Agent 类"""

    def __init__(self, model: str):
        """初始化 Code Agent

        Args:
            model: 模型名称
        """
        self.model: str = model
        self.error_handler = ErrorHandler()
        self.security_manager = SecurityManager()
        self.api_key: str = get_env_var(
            "API_KEY",
            "API key 未设置，请通过环境变量 API_KEY 设置",
        )
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        # 初始化工具字典
        self.tools: dict[str, Any] = {}

        # 导入所有工具模块，确保装饰器被执行
        from code_agent.tools import (
            write_tool,
            read_tool,
            search_tool,
            edit_tool,
            bash_tool,
            glob_tool,
            grep_tool,
        )

        try:
            from code_agent.tools import rag_tool
        except Exception:
            pass

        # 根据配置启用工具
        for tool_name in config.enabled_tools:
            try:
                # 创建工具实例
                if tool_name in ["search_web"]:
                    # 不需要 base_dir 的工具
                    tool_instance = ToolManager.create_tool_instance(tool_name)
                else:
                    # 需要 base_dir 的工具
                    tool_instance = ToolManager.create_tool_instance(tool_name)

                if tool_instance:
                    self.tools[tool_name] = tool_instance
            except Exception as e:
                pass

    @staticmethod
    def create(platform: str, model: str) -> "CodeAgent":
        """创建 Code Agent 实例

        Args:
            platform: 平台类型，可选值: "bailian"
            model: 模型名称

        Returns:
            Code Agent 实例
        """
        if platform != "bailian":
            raise ValueError(f"不支持的平台类型: {platform}")
        return CodeAgent(model)

    def execute_task(self, task: str) -> str:
        """执行任务

        Args:
            task: 任务描述

        Returns:
            执行结果
        """
        try:
            # 检查任务安全性
            if not self.security_manager.check_task(task):
                return "任务包含不安全内容，无法执行"

            # 构建 ReAct 模式的消息
            messages = self._build_react_messages(task)

            # ReAct 循环
            cycle_count = 0
            while cycle_count < config.react_max_cycles:
                # 调用模型
                response = self._call_model(messages)

                # 处理响应
                result, updated_messages = self._process_response(response, messages)

                # 如果有结果，返回结果
                if result:
                    return result

                # 更新消息列表，准备下一次循环
                messages = updated_messages

                cycle_count += 1

            # 循环次数超过限制
            return f"执行超时: 达到最大循环次数 {config.react_max_cycles}"

        except Exception as e:
            error_message = self.error_handler.handle_error(e)
            return f"执行错误: {error_message}"

    def _build_react_messages(self, task: str) -> Iterable[ChatCompletionMessageParam]:
        """构建 ReAct 模式的消息

        Args:
            task: 任务描述

        Returns:
            消息列表
        """
        # 构建工具信息部分
        tools_info = []
        for tool_name, tool in self.tools.items():
            tools_info.append(f"- {tool_name}: {tool.description()}")
            params = tool.parameters()
            if isinstance(params, dict) and "properties" in params:
                properties = params["properties"]
                for param_name, param_info in properties.items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "string")
                    tools_info.append(
                        f"  - {param_name}: {param_desc} (类型: {param_type})"
                    )

        tools_info_str = "\n".join(tools_info)

        system_prompt = f"""你是一个智能代码助手，擅长解决各种编程问题。

## 核心能力
- 代码生成与修改
- 文件操作与管理
- 终端命令执行
- 内容搜索与分析
- 网络信息检索

## 工作流程
1. **思考**：分析任务需求，确定解决方案
2. **行动**：调用工具，使用 JSON 格式，并用 XML 标签包裹
3. **观察**：记录工具执行结果
4. **结论**：基于结果总结完成情况

## 工具使用
你可以使用以下工具：
{tools_info_str}

## 输出格式
请严格按照以下格式输出：

1. **思考**：分析任务，决定下一步行动
2. **行动**：调用工具，使用 XML 标签包裹的 JSON 格式
   <tool_call>
   {{"name": "工具名称", "parameters": {{"参数名": "参数值"}}}}
   </tool_call>
3. **观察**：记录工具执行结果
4. **结论**：基于观察结果，总结任务执行情况

## 重要注意事项
- **标签格式**：请确保使用正确的标签格式 `<tool_call>` 和 `</tool_call>`，不要返回错误的标签格式如 `</tool_call></tool_call>`
- **JSON 格式**：确保 JSON 格式正确，工具调用参数符合要求
- **标签位置**：每个工具调用应该被正确的 `<tool_call>` 和 `</tool_call>` 标签包裹
- **内容清晰**：工具调用的内容应该清晰明确，不要包含多余的标签或字符

确保你的输出严格遵循上述格式要求。
"""

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": task,
            },
        ]

        return messages

    def _build_tools_info(self) -> Iterable[ChatCompletionToolUnionParam]:
        """构建工具信息

        Returns:
            工具信息列表
        """
        tools: list[ChatCompletionToolUnionParam] = []
        for tool_name, tool in self.tools.items():
            tool_info: ChatCompletionToolUnionParam = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description(),
                    "parameters": tool.parameters(),
                },
            }
            tools.append(tool_info)
        return tools

    def _call_model(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatCompletion:
        """调用模型

        Args:
            messages: 消息列表

        Returns:
            模型响应
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return completion

    def _process_response(
        self,
        completion: ChatCompletion,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> tuple[str, list[ChatCompletionMessageParam]]:
        """处理模型响应

        Args:
            completion: 模型响应
            messages: 消息列表

        Returns:
            处理后的结果和更新后的消息列表
        """
        # 获取响应消息
        message = completion.choices[0].message

        # 提取内容
        content = message.content
        if content:
            # 使用 XML 解析器提取工具调用信息
            tool_calls = self._extract_tool_calls(content)
            if tool_calls:
                for tool_call in tool_calls:
                    try:
                        # 解析工具调用 JSON
                        tool_data = json.loads(tool_call)
                        tool_name = tool_data.get("name")
                        parameters = tool_data.get("parameters", {})

                        # 执行工具
                        if tool_name and tool_name in self.tools:
                            tool_result = self.tools[tool_name].run(**parameters)

                            # 转换为列表以便修改
                            messages_list = list(messages)

                            # 添加工具调用消息
                            messages_list.append(
                                {
                                    "role": "assistant",
                                    "content": content,
                                }
                            )

                            # 添加工具执行结果消息
                            messages_list.append(
                                {
                                    "role": "user",
                                    "content": f"工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}",
                                }
                            )

                            # 返回工具执行结果和更新后的消息列表
                            return "", messages_list
                    except Exception as e:
                        # 解析错误，继续处理
                        pass

            # 提取结论
            conclusion_start = content.find("## 结论")
            if conclusion_start != -1:
                return content[conclusion_start:], list(messages)
            return content, list(messages)

        return "模型未返回有效响应", list(messages)

    def _extract_tool_calls(self, content: str) -> list[str]:
        """使用 XML 解析器提取工具调用信息

        Args:
            content: 模型响应内容

        Returns:
            工具调用信息列表
        """
        # 首先尝试匹配正确的标签格式
        pattern = r"<tool_call>([\s\S]*?)</tool_call>"
        matches = re.findall(pattern, content)

        # 如果没有找到，尝试匹配错误的标签格式
        if not matches:
            # 匹配可能的错误标签格式，如 </tool_call></tool_call>
            pattern = r"</?tool_call>([\s\S]*?)</?tool_call>"
            matches = re.findall(pattern, content)

        # 清理匹配结果，移除可能的多余标签
        cleaned_matches = []
        for match in matches:
            # 移除可能的标签残留在内容中
            cleaned_match = re.sub(r"</?tool_call>", "", match).strip()
            if cleaned_match:
                cleaned_matches.append(cleaned_match)

        return cleaned_matches

    def build_enhanced_prompt(
        self, task: str, user_context=None, project_context=None, session_context=None
    ) -> str:
        """构建增强的提示词

        Args:
            task: 任务描述
            user_context: 用户上下文管理器
            project_context: 项目上下文管理器
            session_context: 会话上下文管理器

        Returns:
            增强的提示词
        """
        prompt_parts = []

        # 添加用户上下文
        if user_context:
            user_summary = user_context.get_context_summary()
            if user_summary:
                prompt_parts.append("用户上下文:")
                prompt_parts.append(user_summary)
                prompt_parts.append("")

        # 添加项目上下文
        if project_context:
            project_summary = project_context.get_project_summary()
            if project_summary:
                prompt_parts.append("项目上下文:")
                prompt_parts.append(project_summary)
                prompt_parts.append("")

        # 添加会话上下文
        if session_context:
            session_context_str = session_context.get_context()
            if session_context_str:
                prompt_parts.append("会话上下文:")
                prompt_parts.append(session_context_str)
                prompt_parts.append("")

        # 添加任务
        prompt_parts.append("任务:")
        prompt_parts.append(task)

        return "\n".join(prompt_parts)

    def list_enabled_tools(self) -> str:
        """列出所有启用的工具

        Returns:
            工具列表字符串
        """
        if not self.tools:
            return "没有启用的工具"

        tools_info = []
        tools_info.append("已启用的工具:")
        for tool_name, tool in self.tools.items():
            tools_info.append(f"- {tool_name}: {tool.description()}")

        return "\n".join(tools_info)
