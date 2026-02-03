"""LLM provider interfaces and implementations."""

import importlib.util
from typing import Any, cast

from showrunner.providers.base import BaseLLMProvider, LLMProviderProtocol
from showrunner.providers.rule_based import RuleBasedProvider

AnthropicProvider: type[Any] | None

__all__ = ["BaseLLMProvider", "LLMProviderProtocol", "RuleBasedProvider"]

# Conditionally export AnthropicProvider if dependencies are installed
if importlib.util.find_spec("langchain_anthropic"):
    try:
        from showrunner.providers import (
            anthropic as _anthropic,  # type: ignore[reportMissingImports]
        )
    except Exception:
        AnthropicProvider = None
    else:
        AnthropicProvider = cast(
            "type[Any]",
            _anthropic.AnthropicProvider,  # type: ignore[reportUnknownMemberType]
        )
        __all__.append("AnthropicProvider")
else:
    AnthropicProvider = None
