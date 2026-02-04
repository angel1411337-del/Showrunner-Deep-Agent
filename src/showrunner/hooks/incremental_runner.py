"""Run incremental pipeline updates for passive hooks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from showrunner.pipeline.orchestrator import PipelineConfig, PipelineState, ShowrunnerPipeline


def resolve_corpus_root(repo_root: Path) -> Path:
    env_value = os.getenv("SHOWRUNNER_CORPUS_DIR")
    if env_value:
        return Path(env_value)
    return repo_root / "corpus"


def resolve_output_dir(repo_root: Path) -> Path:
    env_value = os.getenv("SHOWRUNNER_OUTPUT_DIR")
    if env_value:
        return Path(env_value)
    return repo_root / "out"


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
