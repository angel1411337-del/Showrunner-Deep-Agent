"""Mirrored tool wrapper that stores large outputs in memory."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from showrunner.rlm.memory_store import MemoryStore


class ToolCallable(Protocol):
    def __call__(self, **kwargs: Any) -> Any: ...


class MirroredTool:
    """Wrap a tool to resolve pointers and store large outputs."""

    def __init__(
        self,
        *,
        name: str,
        tool: ToolCallable,
        memory_store: MemoryStore,
        max_inline_chars: int = 2000,
    ) -> None:
        if max_inline_chars < 1:
            raise ValueError("max_inline_chars must be >= 1")
        self._name = name
        self._tool = tool
        self._memory = memory_store
        self._max_inline_chars = max_inline_chars

    def __call__(self, **kwargs: Any) -> Any:
        resolved = self._memory.resolve(kwargs)
        result = self._tool(**resolved)
        return self._post_process(result)

    def _post_process(self, value: Any) -> Any:
        if self._should_store(value):
            return self._memory.put(tool_name=self._name, value=value)
        return value

    def _should_store(self, value: Any) -> bool:
        size = self._estimate_size(value)
        return size > self._max_inline_chars

    def _estimate_size(self, value: Any) -> int:
        if isinstance(value, str):
            return len(value)
        if isinstance(value, Mapping):
            typed_value = cast("Mapping[str, Any]", value)
            mapping_value: Mapping[str, Any] = {str(k): v for k, v in typed_value.items()}
            try:
                return len(json.dumps(mapping_value))
            except TypeError:
                return len(str(mapping_value))
        if isinstance(value, list):
            list_value: list[Any] = list(cast("list[Any]", value))
            try:
                return len(json.dumps(list_value))
            except TypeError:
                return len(str(list_value))
        return len(str(value))
