"""Simple REPL-style executor for tool-based traversal steps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class ToolCallable(Protocol):
    def __call__(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class RLMToolCall:
    name: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class RLMTraceEntry:
    name: str
    parameters: dict[str, Any]
    output: Any


@dataclass(frozen=True)
class RLMRunResult:
    outputs: list[Any]
    trace: list[RLMTraceEntry]
    remaining_budget: int


class RLMExecutor:
    """Execute a bounded sequence of tool calls with trace capture."""

    def __init__(self, *, tools: Mapping[str, ToolCallable], max_steps: int = 8) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self._tools = dict(tools)
        self._max_steps = max_steps

    def run(self, calls: Sequence[RLMToolCall]) -> RLMRunResult:
        if len(calls) > self._max_steps:
            raise ValueError("Tool call budget exceeded")

        outputs: list[Any] = []
        trace: list[RLMTraceEntry] = []

        for call in calls:
            tool = self._tools.get(call.name)
            if tool is None:
                raise ValueError(f"Unknown tool: {call.name}")
            output = tool(**call.parameters)
            outputs.append(output)
            trace.append(RLMTraceEntry(name=call.name, parameters=call.parameters, output=output))

        remaining = self._max_steps - len(calls)
        return RLMRunResult(outputs=outputs, trace=trace, remaining_budget=remaining)
