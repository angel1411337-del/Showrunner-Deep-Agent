"""Tool wrappers for agent runtimes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from showrunner.agent.harness import AgentHarness, AgentRunResult

if TYPE_CHECKING:
    from pathlib import Path


def run_pipeline(*, input_source: Path, output_dir: Path) -> AgentRunResult:
    harness = AgentHarness()
    return harness.run_pipeline(input_source=input_source, output_dir=output_dir)


def list_artifacts(*, output_dir: Path) -> list[str]:
    harness = AgentHarness()
    return harness.list_artifacts(output_dir=output_dir)


def read_artifact(*, output_dir: Path, relative_path: str) -> str:
    harness = AgentHarness()
    return harness.read_artifact(output_dir=output_dir, relative_path=relative_path)
