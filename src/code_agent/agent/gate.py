from opentelemetry import trace
from openai import AsyncOpenAI, Omit, omit
from code_agent.core.config import GateConfig
from code_agent import monitoring
from typing import Iterable
from openai.types.chat import (
    ChatCompletionToolUnionParam,
    ChatCompletionMessageParam,
    ChatCompletion,
)

_tracer = monitoring.get_tracer(__name__)
_logger = monitoring.get_logger(__name__)


class ModelGate:
    def __init__(self, model_config: GateConfig):
        self.client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
        )
        self._model = model_config.model

    @_tracer.start_as_current_span("call_model")
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
        span = trace.get_current_span()
        usage = result.usage
        if usage:
            span.set_attribute("total_tokens", usage.total_tokens)
            span.set_attribute("prompt_tokens", usage.prompt_tokens)
            span.set_attribute("completion_tokens", usage.completion_tokens)
        return result
