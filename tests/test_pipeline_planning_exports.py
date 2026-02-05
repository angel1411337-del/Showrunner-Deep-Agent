"""Tests for integrated planning exports in the main pipeline."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

if TYPE_CHECKING:
    from pathlib import Path


def _write_sample_corpus(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "book1.txt").write_text(
        "\n".join(
            [
                "Jon Snow swore an oath to return to Winterfell.",
                "Who had sent the letter to House Stark?",
                "The journey ahead would be long.",
            ]
        ),
        encoding="utf-8",
    )


def test_run_writes_planning_exports(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    config = PipelineConfig(input_source=input_dir, output_dir=output_dir)
    state, _manifest = ShowrunnerPipeline(config=config).run()

    assert state.get("error") is None

    outline_path = output_dir / "exports" / "master_outline_books_6_7.md"
    reveals_path = output_dir / "exports" / "mysteries_reveals_table.csv"
    twist_path = output_dir / "exports" / "twist_bank.md"

    assert outline_path.exists()
    assert reveals_path.exists()
    assert twist_path.exists()

    assert outline_path.read_text(encoding="utf-8").startswith("# Master Outline")
    assert "mystery_obligation_id" in reveals_path.read_text(encoding="utf-8")
    assert twist_path.read_text(encoding="utf-8").startswith("# Twist Bank")


def test_run_writes_planning_structured_stores(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    config = PipelineConfig(input_source=input_dir, output_dir=output_dir)
    state, _manifest = ShowrunnerPipeline(config=config).run()

    assert state.get("error") is None

    outline_store = output_dir / "plans" / "outline.json"
    reveals_store = output_dir / "plans" / "reveals.json"
    twists_store = output_dir / "plans" / "twists.json"

    assert outline_store.exists()
    assert reveals_store.exists()
    assert twists_store.exists()

    outline_data = json.loads(outline_store.read_text(encoding="utf-8"))
    reveals_data = json.loads(reveals_store.read_text(encoding="utf-8"))
    twists_data = json.loads(twists_store.read_text(encoding="utf-8"))

    assert isinstance(outline_data, list)
    assert isinstance(reveals_data, list)
    assert isinstance(twists_data, list)
