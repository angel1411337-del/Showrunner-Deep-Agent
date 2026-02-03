"""Rule-based provider used as an offline default."""

from __future__ import annotations

from showrunner.providers.base import BaseLLMProvider


class RuleBasedProvider(BaseLLMProvider):
    """Simple rule-based provider that returns deterministic defaults."""

    def __init__(self) -> None:
        super().__init__(model_name="rule-based")

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        return ""

    def complete_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ):
        raise NotImplementedError(
            "Rule-based provider does not support structured completion"
        )
