"""LLM provider interfaces and implementations."""

import importlib.util
from typing import Any, cast

from showrunner.providers.base import BaseLLMProvider, LLMProviderProtocol
from showrunner.providers.rule_based import RuleBasedProvider

AnthropicProvider: type[Any] | None

__all__ = ["BaseLLMProvider", "LLMProviderProtocol", "RuleBasedProvider"]

# Conditionally export AnthropicProvider if anthropic is installed
if importlib.util.find_spec("showrunner.providers.anthropic"):
    from showrunner.providers import anthropic as _anthropic  # type: ignore[reportMissingImports]

    AnthropicProvider = cast(
        "type[Any]",
        _anthropic.AnthropicProvider,  # type: ignore[reportUnknownMemberType]
    )
    __all__.append("AnthropicProvider")
else:
    AnthropicProvider = None
