"""Anthropic LLM provider implementation via LangChain."""

from __future__ import annotations

import inspect
import os
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar, cast

from showrunner.providers.base import BaseLLMProvider

try:
    from langchain_anthropic import ChatAnthropic as _ChatAnthropic
    from langchain_core.messages import HumanMessage as _HumanMessage
    from langchain_core.messages import SystemMessage as _SystemMessage
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "langchain-anthropic is required for AnthropicProvider. "
        "Install with `uv sync --extra llm` or `pip install showrunner[llm]`."
    ) from exc

ChatAnthropic = cast("Any", _ChatAnthropic)
HumanMessage = cast("Any", _HumanMessage)
SystemMessage = cast("Any", _SystemMessage)

T = TypeVar("T")


def _stringify_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, Sequence):
        parts: list[str] = []
        for item in cast("Sequence[object]", content):
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                mapping = cast("Mapping[str, object]", item)
                text = mapping.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif text is not None:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider wrapper using LangChain's ChatAnthropic."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "claude-3-5-sonnet-latest",
    ) -> None:
        super().__init__(model_name=model_name)
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def _build_client(self, *, temperature: float, max_tokens: int) -> Any:
        if not self._api_key:
            raise ValueError(
                "Anthropic API key is required. Provide api_key or set ANTHROPIC_API_KEY."
            )
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            signature = inspect.signature(ChatAnthropic.__init__)
        except (TypeError, ValueError):
            signature = None
        if signature is not None:
            if "anthropic_api_key" in signature.parameters:
                kwargs["anthropic_api_key"] = self._api_key
            elif "api_key" in signature.parameters:
                kwargs["api_key"] = self._api_key
        else:
            kwargs["anthropic_api_key"] = self._api_key
        return ChatAnthropic(**kwargs)

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        client = self._build_client(temperature=temperature, max_tokens=max_tokens)
        messages: list[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        result = client.invoke(messages)
        return _stringify_content(getattr(result, "content", result))

    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        client = self._build_client(temperature=temperature, max_tokens=4096)
        messages: list[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        structured_builder = client.with_structured_output
        structured = structured_builder(response_model)
        result = structured.invoke(messages)
        if isinstance(result, response_model):
            return result
        validator = getattr(response_model, "model_validate", None)
        if callable(validator):
            return cast("T", validator(result))
        return cast("T", result)
