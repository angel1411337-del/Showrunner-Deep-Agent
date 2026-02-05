"""Deepagents runtime scaffold using the existing tool wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from showrunner.agent import tools

if TYPE_CHECKING:
    from pathlib import Path

    from showrunner.agent.harness import AgentRunResult


class DeepagentsRuntime:
    """Scaffolded deepagents runtime that delegates to pipeline tools for now."""

    def __init__(self) -> None:
        self._available = _deepagents_available()

    @property
    def available(self) -> bool:
        return self._available

    def run(self, *, input_source: Path, output_dir: Path) -> AgentRunResult:
        return tools.run_pipeline(input_source=input_source, output_dir=output_dir)

    def list_artifacts(self, *, output_dir: Path) -> list[str]:
        return tools.list_artifacts(output_dir=output_dir)

    def read_artifact(self, *, output_dir: Path, relative_path: str) -> str:
        return tools.read_artifact(output_dir=output_dir, relative_path=relative_path)


def _deepagents_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("deepagents") is not None
