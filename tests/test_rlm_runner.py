from __future__ import annotations

from showrunner.rlm.rlm_runner import RLMRunner


def test_rlm_runner_executes_program_and_tools() -> None:
    def echo(*, value: str) -> str:
        return value

    runner = RLMRunner(tools={"echo": echo}, max_inline_chars=100)
    result = runner.run_program(prompt="alpha", code="env.emit_tool_call('echo', value='hi')")

    assert result.outputs == ["hi"]


def test_rlm_runner_stores_large_output() -> None:
    def big() -> str:
        return "x" * 50

    runner = RLMRunner(tools={"big": big}, max_inline_chars=10)
    result = runner.run_program(prompt="beta", code="env.emit_tool_call('big')")

    pointer = result.outputs[0]
    assert runner.memory_store.is_pointer(pointer)
    assert runner.memory_store.get(pointer) == "x" * 50
