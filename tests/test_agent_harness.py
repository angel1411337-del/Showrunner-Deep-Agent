"""Tests-first coverage for minimal agent harness runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from showrunner.agent.harness import AgentHarness, runtime_capabilities

if TYPE_CHECKING:
    from pathlib import Path

    from showrunner.agent.harness import AgentRunResult


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


def test_runtime_capabilities_reports_expected_keys() -> None:
    caps = runtime_capabilities()

    assert "langgraph" in caps
    assert "langchain" in caps
    assert "deepagents" in caps
    assert isinstance(caps["langgraph"], bool)
    assert isinstance(caps["langchain"], bool)
    assert isinstance(caps["deepagents"], bool)


def test_harness_run_pipeline_produces_v0_exports(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    harness = AgentHarness()
    result: AgentRunResult = harness.run_pipeline(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    assert result.error is None
    assert (output_dir / "exports" / "Unresolved_Threads_Dossier.md").exists()
    assert (output_dir / "exports" / "master_outline_books_6_7.md").exists()
    assert (output_dir / "exports" / "mysteries_reveals_table.csv").exists()
    assert (output_dir / "exports" / "twist_bank.md").exists()


def test_harness_lists_artifacts_relative_to_output_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    harness = AgentHarness()
    harness.run_pipeline(input_source=input_dir, output_dir=output_dir)

    artifacts = harness.list_artifacts(output_dir=output_dir)

    assert "exports/Unresolved_Threads_Dossier.md" in artifacts
    assert "exports/master_outline_books_6_7.md" in artifacts
    assert "exports/mysteries_reveals_table.csv" in artifacts
    assert "exports/twist_bank.md" in artifacts


def test_harness_read_artifact_returns_text(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    harness = AgentHarness()
    harness.run_pipeline(input_source=input_dir, output_dir=output_dir)

    content = harness.read_artifact(
        output_dir=output_dir,
        relative_path="exports/Unresolved_Threads_Dossier.md",
    )

    assert content.startswith("# Unresolved Threads Dossier")


def test_harness_read_artifact_raises_for_missing_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    harness = AgentHarness()

    with pytest.raises(FileNotFoundError):
        harness.read_artifact(output_dir=output_dir, relative_path="exports/missing.md")
