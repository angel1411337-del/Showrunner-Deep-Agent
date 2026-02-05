from __future__ import annotations

from showrunner.rlm.memory_store import MemoryStore
from showrunner.rlm.mirrored_tool import MirroredTool


def test_mirrored_tool_stores_large_output() -> None:
    store = MemoryStore()

    def tool(*, text: str) -> str:
        return text

    mirrored = MirroredTool(
        name="echo",
        tool=tool,
        memory_store=store,
        max_inline_chars=5,
    )

    result = mirrored(text="x" * 10)

    assert store.is_pointer(result)
    assert store.get(result) == "x" * 10


def test_mirrored_tool_resolves_pointer_inputs() -> None:
    store = MemoryStore()
    pointer = store.put(tool_name="seed", value="resolved")
    seen = {}

    def tool(*, text: str) -> str:
        seen["value"] = text
        return "ok"

    mirrored = MirroredTool(name="echo", tool=tool, memory_store=store, max_inline_chars=20)
    output = mirrored(text=pointer)

    assert output == "ok"
    assert seen["value"] == "resolved"


def test_mirrored_tool_stores_dict_output_by_key() -> None:
    store = MemoryStore()

    def tool() -> dict[str, str]:
        return {"a": "alpha", "b": "beta"}

    mirrored = MirroredTool(name="dict_tool", tool=tool, memory_store=store, max_inline_chars=1)
    result = mirrored()

    assert result["a"].startswith("mem://")
    assert store.get(result["a"]) == "alpha"
    assert store.get(result["b"]) == "beta"
