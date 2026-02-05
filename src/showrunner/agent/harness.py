"""Minimal agent harness over the existing LangGraph pipeline."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

if TYPE_CHECKING:
    from pathlib import Path


def runtime_capabilities() -> dict[str, bool]:
    """Return runtime availability flags for core orchestration layers."""
    return {
        "langgraph": importlib.util.find_spec("langgraph") is not None,
        "langchain": importlib.util.find_spec("langchain") is not None,
        "deepagents": importlib.util.find_spec("deepagents") is not None,
    }


@dataclass(frozen=True)
class AgentRunResult:
    """Structured result for a harness-triggered pipeline run."""

    status: Literal["completed", "failed"]
    error: str | None
    output_dir: Path
    run_manifest_path: Path
    export_paths: list[Path]


class AgentHarness:
    """Small orchestration wrapper for pipeline execution and artifact access."""

    def run_pipeline(self, input_source: Path, output_dir: Path) -> AgentRunResult:
        config = PipelineConfig(input_source=input_source, output_dir=output_dir)
        state, _manifest = ShowrunnerPipeline(config=config).run()
        exports_dir = output_dir / "exports"
        export_paths = sorted(path for path in exports_dir.glob("*") if path.is_file())
        status: Literal["completed", "failed"] = "failed" if state.get("error") else "completed"
        return AgentRunResult(
            status=status,
            error=state.get("error"),
            output_dir=output_dir,
            run_manifest_path=output_dir / "run_manifest.json",
            export_paths=export_paths,
        )

    def list_artifacts(self, output_dir: Path) -> list[str]:
        if not output_dir.exists():
            return []
        files = [path for path in output_dir.rglob("*") if path.is_file()]
        root = output_dir.resolve()
        return sorted(path.resolve().relative_to(root).as_posix() for path in files)

    def read_artifact(self, output_dir: Path, relative_path: str) -> str:
        root = output_dir.resolve()
        artifact_path = (output_dir / relative_path).resolve()
        try:
            artifact_path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Artifact path escapes output directory") from exc
        if not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path}")
        return artifact_path.read_text(encoding="utf-8")
