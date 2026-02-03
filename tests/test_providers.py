"""Tests for LLM provider interfaces and implementations."""

import pytest
from pydantic import BaseModel

from showrunner.providers import (
    BaseLLMProvider,
    LLMProviderProtocol,
    RuleBasedProvider,
)


class SampleResponseModel(BaseModel):
    """Sample Pydantic model for testing structured completions."""

    name: str
    value: int


class TestLLMProviderProtocol:
    """Tests for LLMProviderProtocol interface definition."""

    def test_protocol_is_runtime_checkable(self):
        """Protocol must be decorated with @runtime_checkable."""
        assert hasattr(LLMProviderProtocol, "__protocol_attrs__") or hasattr(
            LLMProviderProtocol, "_is_runtime_protocol"
        )

    def test_protocol_defines_model_name_property(self):
        """Protocol must define model_name property."""
        # Protocol attributes are accessible via __protocol_attrs__ or checking annotations
        assert "model_name" in dir(LLMProviderProtocol)

    def test_protocol_defines_complete_method(self):
        """Protocol must define complete method."""
        assert hasattr(LLMProviderProtocol, "complete")
        assert callable(getattr(LLMProviderProtocol, "complete", None))

    def test_protocol_defines_complete_structured_method(self):
        """Protocol must define complete_structured method."""
        assert hasattr(LLMProviderProtocol, "complete_structured")
        assert callable(getattr(LLMProviderProtocol, "complete_structured", None))


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract base class."""

    def test_base_provider_is_abstract(self):
        """BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider("test-model")  # type: ignore[abstract]

    def test_base_provider_stores_model_name(self):
        """Subclasses should have access to model_name."""

        class ConcreteProvider(BaseLLMProvider):
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
                return response_model()

        provider = ConcreteProvider("gpt-4")
        assert provider.model_name == "gpt-4"


class TestRuleBasedProvider:
    """Tests for RuleBasedProvider mock implementation."""

    def test_rule_based_provider_initialization(self):
        """RuleBasedProvider initializes with 'rule-based' model name."""
        provider = RuleBasedProvider()
        assert provider.model_name == "rule-based"

    def test_rule_based_provider_complete_returns_empty_string(self):
        """RuleBasedProvider.complete returns empty string."""
        provider = RuleBasedProvider()
        result = provider.complete("Test prompt")
        assert result == ""

    def test_rule_based_provider_complete_with_all_parameters(self):
        """RuleBasedProvider.complete accepts all standard parameters."""
        provider = RuleBasedProvider()
        result = provider.complete(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant.",
            temperature=0.5,
            max_tokens=1024,
        )
        assert result == ""

    def test_rule_based_provider_complete_structured_raises_not_implemented(self):
        """RuleBasedProvider.complete_structured raises NotImplementedError."""
        provider = RuleBasedProvider()
        with pytest.raises(NotImplementedError) as exc_info:
            provider.complete_structured(
                prompt="Test prompt",
                response_model=SampleResponseModel,
            )
        assert "Rule-based provider does not support structured completion" in str(exc_info.value)

    def test_rule_based_provider_implements_protocol(self):
        """RuleBasedProvider must satisfy LLMProviderProtocol."""
        provider = RuleBasedProvider()
        assert isinstance(provider, LLMProviderProtocol)

    def test_rule_based_provider_is_subclass_of_base(self):
        """RuleBasedProvider inherits from BaseLLMProvider."""
        assert issubclass(RuleBasedProvider, BaseLLMProvider)
