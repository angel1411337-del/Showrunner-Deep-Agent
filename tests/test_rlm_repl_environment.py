from __future__ import annotations

import pytest

from showrunner.rlm.repl_environment import ReplEnvironment


def test_repl_environment_snippet_and_emit() -> None:
    env = ReplEnvironment(prompt="hello world")

    assert env.length() == 11
    assert env.snippet(0, 5) == "hello"

    env.emit_tool_call("echo", value="hi")
    calls = env.consume_tool_calls()

    assert len(calls) == 1
    assert calls[0].name == "echo"
    assert calls[0].parameters == {"value": "hi"}


def test_repl_environment_recurse_calls_callback() -> None:
    seen = {}

    def recurse_fn(text: str) -> str:
        seen["text"] = text
        return "ok"

    env = ReplEnvironment(prompt="abc", recurse_fn=recurse_fn)
    assert env.recurse("snippet") == "ok"
    assert seen["text"] == "snippet"


def test_repl_environment_recurse_requires_callback() -> None:
    env = ReplEnvironment(prompt="abc")

    with pytest.raises(RuntimeError):
        env.recurse("snippet")
