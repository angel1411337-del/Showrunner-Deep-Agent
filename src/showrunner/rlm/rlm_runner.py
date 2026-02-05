"""RLM runner that executes REPL code and tool calls."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from showrunner.rlm.memory_store import MemoryStore
from showrunner.rlm.mirrored_tool import MirroredTool, ToolCallable
from showrunner.rlm.repl_environment import SAFE_BUILTINS, ReplEnvironment
from showrunner.rlm.repl_executor import RLMExecutor, RLMRunResult

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class RLMRunner:
    """Execute REPL code, collect tool calls, and run them with memory pointers."""

    def __init__(
        self,
        *,
        tools: Mapping[str, ToolCallable],
        memory_store: MemoryStore | None = None,
        max_inline_chars: int = 2000,
        max_steps: int = 8,
        safe_builtins: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self._memory_store = memory_store or MemoryStore()
        self._mirrored_tools = {
            name: MirroredTool(
                name=name,
                tool=tool,
                memory_store=self._memory_store,
                max_inline_chars=max_inline_chars,
            )
            for name, tool in tools.items()
        }
        self._max_steps = max_steps
        self._safe_builtins = safe_builtins or SAFE_BUILTINS

    @property
    def memory_store(self) -> MemoryStore:
        return self._memory_store

    def run_program(self, *, prompt: str, code: str) -> RLMRunResult:
        env = ReplEnvironment(prompt=prompt)
        self._exec_code(code=code, env=env)
        calls = env.consume_tool_calls()
        executor = RLMExecutor(tools=self._mirrored_tools, max_steps=self._max_steps)
        return executor.run(calls)

    def _exec_code(self, *, code: str, env: ReplEnvironment) -> None:
        globals_dict: dict[str, Any] = {"env": env, "__builtins__": self._safe_builtins}
        exec(code, globals_dict, {})
