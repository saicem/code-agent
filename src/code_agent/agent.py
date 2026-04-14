#!/usr/bin/env python3
"""
Code Agent 类
"""

import json
from code_agent.error_handling import ErrorHandler
from code_agent.security import SecurityManager
from code_agent.tools import (
    WriteTool,
    ReadTool,
    SearchTool,
    EditTool,
    BashTool,
    GlobTool,
    GrepTool,
)
from code_agent.model_gate import ModelGate


class CodeAgent:
    """Code Agent 类"""

    def __init__(self, model: str, base_dir: str = "."):
        """初始化 Code Agent

        Args:
            model: 模型名称
            base_dir: 基础目录
        """
        self.model = model
        self.base_dir = base_dir
        self.error_handler = ErrorHandler()
        self.security_manager = SecurityManager()
        self.model_gate = ModelGate(model)
        self.tools = {
            "write_file": WriteTool(base_dir),
            "read_file": ReadTool(base_dir),
            "search_web": SearchTool(),
            "edit_file": EditTool(base_dir),
            "run_bash": BashTool(base_dir),
            "search_files": GlobTool(base_dir),
            "search_content": GrepTool(base_dir),
        }

    @staticmethod
    def create(platform: str, model: str, base_dir: str = ".") -> "CodeAgent":
        """创建 Code Agent 实例

        Args:
            platform: 平台类型，可选值: "bailian"
            model: 模型名称
            base_dir: 基础目录

        Returns:
            Code Agent 实例
        """
        if platform != "bailian":
            raise ValueError(f"不支持的平台类型: {platform}")
        return CodeAgent(model, base_dir)

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

            # 构建 ReAct 模式的提示词
            prompt = self._build_react_prompt(task)

            # 调用模型
            response = self.model_gate.call_model(prompt)

            # 处理响应
            result = self._process_response(response)

            return result

        except Exception as e:
            error_message = self.error_handler.handle_error(e)
            return f"执行错误: {error_message}"

    def _build_react_prompt(self, task: str) -> str:
        """构建 ReAct 模式的提示词

        Args:
            task: 任务描述

        Returns:
            提示词字符串
        """
        # 构建工具描述
        tools_description = self._get_tools_description()

        prompt = f"""你是一个帮助用户完成任务的助手。

## 工具

{tools_description}

## 任务

{task}

## 要求

请按照以下格式进行思考和操作：

1. **思考**：分析任务，决定下一步行动
2. **行动**：调用工具，格式为：
   ```json
   {"tool_call": {"name": "工具名称", "parameters": {"参数名": "参数值"}}}
   ```
3. **观察**：记录工具执行结果
4. **结论**：基于观察结果，总结任务执行情况

请严格按照上述格式输出，确保 JSON 格式正确。
"""

        return prompt

    def _get_tools_description(self) -> str:
        """获取工具描述

        Returns:
            工具描述字符串
        """
        tools_desc = []
        for tool_name, tool in self.tools.items():
            tools_desc.append(f"- {tool_name}: {tool.description()}")
            tools_desc.append(f"  参数: {json.dumps(tool.parameters(), indent=2)}")
        return "\n".join(tools_desc)

    def _process_response(self, response: str) -> str:
        """处理模型响应

        Args:
            response: 模型响应

        Returns:
            处理后的结果
        """
        # 解析 ReAct 格式的响应
        try:
            # 提取工具调用
            tool_call_start = response.find('{"tool_call":')
            if tool_call_start != -1:
                # 提取 JSON
                tool_call_end = response.find("}", tool_call_start)
                if tool_call_end != -1:
                    # 查找匹配的右括号
                    brace_count = 1
                    for i in range(tool_call_start + 1, len(response)):
                        if response[i] == "{":
                            brace_count += 1
                        elif response[i] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                tool_call_end = i
                                break

                    tool_call_json = response[tool_call_start : tool_call_end + 1]
                    tool_call_data = json.loads(tool_call_json)
                    tool_name = tool_call_data["tool_call"]["name"]
                    parameters = tool_call_data["tool_call"]["parameters"]

                    # 执行工具
                    if tool_name in self.tools:
                        tool_result = self.tools[tool_name].run(**parameters)

                        # 构建新的提示词，包含工具执行结果
                        new_prompt = f"""{response}

## 观察

工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}

请继续完成任务，按照思考-行动-观察-结论的格式输出。
"""

                        # 再次调用模型
                        new_response = self.model_gate.call_model(new_prompt)
                        return self._process_response(new_response)

            # 提取结论
            conclusion_start = response.find("## 结论")
            if conclusion_start != -1:
                return response[conclusion_start:]

            return response
        except Exception as e:
            return f"处理响应时出错: {str(e)}\n\n原始响应: {response}"
