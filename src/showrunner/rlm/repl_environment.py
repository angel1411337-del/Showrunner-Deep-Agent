"""REPL-like environment for RLM-style prompt inspection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from showrunner.rlm.repl_executor import RLMToolCall

if TYPE_CHECKING:
    from collections.abc import Callable


class ReplEnvironment:
    """Expose prompt inspection helpers and tool-call collection."""

    def __init__(
        self,
        *,
        prompt: str,
        max_snippet_chars: int = 4000,
        recurse_fn: Callable[[str], Any] | None = None,
    ) -> None:
        if max_snippet_chars < 1:
            raise ValueError("max_snippet_chars must be >= 1")
        self._prompt = prompt
        self._max_snippet_chars = max_snippet_chars
        self._tool_calls: list[RLMToolCall] = []
        self._recurse_fn = recurse_fn

    @property
    def prompt(self) -> str:
        return self._prompt

    def length(self) -> int:
        return len(self._prompt)

    def snippet(self, start: int, end: int) -> str:
        if start < 0 or end < 0 or end < start:
            raise ValueError("Invalid snippet range")
        snippet = self._prompt[start:end]
        if len(snippet) > self._max_snippet_chars:
            raise ValueError("Snippet exceeds max_snippet_chars")
        return snippet

    def search(self, term: str) -> int:
        return self._prompt.find(term)

    def emit_tool_call(self, name: str, **parameters: Any) -> None:
        self._tool_calls.append(RLMToolCall(name=name, parameters=parameters))

    def consume_tool_calls(self) -> list[RLMToolCall]:
        calls = list(self._tool_calls)
        self._tool_calls.clear()
        return calls

    def recurse(self, snippet: str) -> Any:
        if self._recurse_fn is None:
            raise RuntimeError("No recurse function configured")
        return self._recurse_fn(snippet)


SAFE_BUILTINS: dict[str, Callable[..., Any]] = {
    "len": len,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "enumerate": enumerate,
    "list": list,
    "dict": dict,
}
