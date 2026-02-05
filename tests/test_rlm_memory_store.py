from __future__ import annotations

from showrunner.rlm.memory_store import MemoryStore


def test_memory_store_put_and_get_roundtrip() -> None:
    store = MemoryStore()
    pointer = store.put(tool_name="tool", value="x" * 20)

    assert store.is_pointer(pointer)
    assert store.get(pointer) == "x" * 20


def test_memory_store_put_dict_returns_pointers() -> None:
    store = MemoryStore()
    pointers = store.put(tool_name="tool", value={"a": "alpha", "b": "beta"})

    assert isinstance(pointers, dict)
    assert store.is_pointer(pointers["a"])
    assert store.get(pointers["a"]) == "alpha"
    assert store.get(pointers["b"]) == "beta"


def test_memory_store_resolve_replaces_pointers() -> None:
    store = MemoryStore()
    pointer = store.put(tool_name="tool", value="payload")

    resolved = store.resolve({"value": pointer, "items": [pointer]})

    assert resolved["value"] == "payload"
    assert resolved["items"][0] == "payload"
