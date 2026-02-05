"""Runtime memory store for pointer-based tool outputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast


class MemoryStore:
    """Store large tool outputs and reference them via pointer strings."""

    def __init__(self, *, pointer_prefix: str = "mem://") -> None:
        self._pointer_prefix = pointer_prefix
        self._store: dict[str, Any] = {}
        self._counter = 0

    @property
    def pointer_prefix(self) -> str:
        return self._pointer_prefix

    def put(self, *, tool_name: str, value: Any) -> Any:
        if isinstance(value, Mapping):
            typed_value = cast("Mapping[str, Any]", value)
            base_id = self._next_id()
            pointers: dict[str, str] = {}
            for key, entry in typed_value.items():
                key_str = str(key)
                pointer = self._make_pointer(
                    tool_name=tool_name,
                    identifier=base_id,
                    key=key_str,
                )
                self._store[pointer] = entry
                pointers[key_str] = pointer
            return pointers

        pointer = self._make_pointer(tool_name=tool_name, identifier=self._next_id())
        self._store[pointer] = value
        return pointer

    def get(self, pointer: str) -> Any:
        if pointer not in self._store:
            raise KeyError(f"Pointer not found: {pointer}")
        return self._store[pointer]

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str) and self.is_pointer(value):
            return self.get(value)
        if isinstance(value, Mapping):
            typed_value = cast("Mapping[str, Any]", value)
            return {key: self.resolve(entry) for key, entry in typed_value.items()}
        if isinstance(value, list):
            typed_value = cast("list[Any]", value)
            return [self.resolve(entry) for entry in typed_value]
        if isinstance(value, tuple):
            typed_value = cast("tuple[Any, ...]", value)
            return tuple(self.resolve(entry) for entry in typed_value)
        return value

    def is_pointer(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(self._pointer_prefix)

    def _make_pointer(self, *, tool_name: str, identifier: str, key: str | None = None) -> str:
        if key is None:
            return f"{self._pointer_prefix}{tool_name}/{identifier}"
        return f"{self._pointer_prefix}{tool_name}/{identifier}/{key}"

    def _next_id(self) -> str:
        self._counter += 1
        return str(self._counter)
