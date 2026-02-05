from __future__ import annotations

import pytest

from showrunner.rlm.repl_executor import RLMExecutor, RLMToolCall


def test_executor_runs_tool_calls_in_order() -> None:
    calls = []

    def record(*, value: int) -> int:
        calls.append(value)
        return value * 2

    executor = RLMExecutor(tools={"record": record}, max_steps=3)
    result = executor.run(
        [
            RLMToolCall(name="record", parameters={"value": 1}),
            RLMToolCall(name="record", parameters={"value": 3}),
        ]
    )

    assert calls == [1, 3]
    assert result.outputs == [2, 6]
    assert [entry.name for entry in result.trace] == ["record", "record"]
    assert result.remaining_budget == 1


def test_executor_rejects_unknown_tool() -> None:
    executor = RLMExecutor(tools={}, max_steps=1)

    with pytest.raises(ValueError):
        executor.run([RLMToolCall(name="missing", parameters={})])


def test_executor_enforces_step_budget() -> None:
    executor = RLMExecutor(tools={"noop": lambda: None}, max_steps=1)

    with pytest.raises(ValueError):
        executor.run(
            [
                RLMToolCall(name="noop", parameters={}),
                RLMToolCall(name="noop", parameters={}),
            ]
        )
