from typing import Iterable

from openai import AsyncOpenAI, Omit, omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from code_agent import monitoring
from code_agent.core.config import GateConfig

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)


class ModelGate:
    def __init__(self, model_config: GateConfig):
        self.client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
        )
        self._model = model_config.model

    async def call_model(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolUnionParam] | Omit = omit,
    ) -> ChatCompletion:
        result = await self.client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
        )
        return result
