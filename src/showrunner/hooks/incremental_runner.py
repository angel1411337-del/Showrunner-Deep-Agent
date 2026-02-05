"""Run incremental pipeline updates for passive hooks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from showrunner.pipeline.orchestrator import PipelineConfig, PipelineState, ShowrunnerPipeline


def _resolve_environment_id(environment_id: str | None = None) -> str | None:
    return environment_id or os.getenv("SHOWRUNNER_ENV")


def _resolve_environment_root(repo_root: Path, *, environment_id: str | None = None) -> Path:
    resolved = _resolve_environment_id(environment_id)
    if resolved:
        return repo_root / "environments" / resolved
    return repo_root


def resolve_corpus_root(repo_root: Path, *, environment_id: str | None = None) -> Path:
    env_value = os.getenv("SHOWRUNNER_CORPUS_DIR")
    if env_value:
        return Path(env_value)
    environment_root = _resolve_environment_root(repo_root, environment_id=environment_id)
    return environment_root / "corpus"


def resolve_output_dir(repo_root: Path, *, environment_id: str | None = None) -> Path:
    env_value = os.getenv("SHOWRUNNER_OUTPUT_DIR")
    if env_value:
        return Path(env_value)
    environment_root = _resolve_environment_root(repo_root, environment_id=environment_id)
    return environment_root / "out"


def run_incremental(
    changed_files: Iterable[Path],
    *,
    corpus_root: Path,
    output_dir: Path,
) -> PipelineState | None:
    """Run the incremental pipeline for a set of changed files.

    Returns the PipelineState or None when no changes are provided.
    """
    files = list(changed_files)
    if not files:
        return None

    config = PipelineConfig(input_source=corpus_root, output_dir=output_dir)
    pipeline = ShowrunnerPipeline(config=config)
    return pipeline.run_incremental(files)
