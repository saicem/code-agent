from typing import Iterable

from openai import AsyncOpenAI, Omit, omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from code_agent import monitoring
from code_agent.core.config import GateConfig, get_config

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)


class GenAiGate:
    def __init__(self, model_config: GateConfig):
        _logger.info(
            f"初始化 GenAiGate，模型: {model_config.model}, 基础URL: {model_config.base_url}"
        )
        self.client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
        )
        self._model = model_config.model
        _logger.debug("GenAiGate 初始化完成")

    async def call_model(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    ) -> ChatCompletion:
        _logger.debug(f"调用模型: {self._model}")
        _logger.debug(f"消息数量: {len(list(messages))}")

        try:
            result = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                reasoning_effort="low",
            )
            _logger.debug(f"模型调用成功，响应ID: {result.id}")
            return result
        except Exception as e:
            _logger.error(f"模型调用失败: {e}", exc_info=True)
            raise


_gate = GenAiGate(get_config().gate)


def get_gate() -> GenAiGate:
    return _gate
