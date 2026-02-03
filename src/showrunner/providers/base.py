"""Base interfaces for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Protocol for LLM provider implementations."""

    @property
    def model_name(self) -> str:
        """Model name or identifier."""
        ...

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Return a plain text completion."""
        ...

    def complete_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ):
        """Return a structured response coerced into response_model."""
        ...


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Return a plain text completion."""

    @abstractmethod
    def complete_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ):
        """Return a structured response coerced into response_model."""
