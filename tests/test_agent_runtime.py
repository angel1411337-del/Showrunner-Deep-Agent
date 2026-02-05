from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from showrunner.agent import tools
from showrunner.agent.runtime import AgentRuntime, RuntimeMode, parse_runtime_mode

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


def test_parse_runtime_mode_accepts_strings() -> None:
    assert parse_runtime_mode("pipeline") is RuntimeMode.PIPELINE
    assert parse_runtime_mode("langchain") is RuntimeMode.LANGCHAIN
    assert parse_runtime_mode("deepagents") is RuntimeMode.DEEPAGENTS

    with pytest.raises(ValueError):
        parse_runtime_mode("unknown")


def test_parse_runtime_mode_accepts_enum() -> None:
    assert parse_runtime_mode(RuntimeMode.PIPELINE) is RuntimeMode.PIPELINE


def test_agent_runtime_pipeline_runs_pipeline(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    runtime = AgentRuntime(mode="pipeline")
    result = runtime.run(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    assert (output_dir / "exports" / "Unresolved_Threads_Dossier.md").exists()
    assert (output_dir / "exports" / "master_outline_books_6_7.md").exists()
    assert (output_dir / "exports" / "mysteries_reveals_table.csv").exists()
    assert (output_dir / "exports" / "twist_bank.md").exists()


def test_agent_runtime_langchain_runs_pipeline(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    runtime = AgentRuntime(mode="langchain")

    result = runtime.run(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    assert (output_dir / "exports" / "Unresolved_Threads_Dossier.md").exists()


def test_agent_runtime_unsupported_modes_raise(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    runtime = AgentRuntime(mode="deepagents")

    with pytest.raises(NotImplementedError):
        runtime.run(input_source=input_dir, output_dir=output_dir)


def test_agent_tools_run_and_read(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    result = tools.run_pipeline(input_source=input_dir, output_dir=output_dir)
    assert result.status == "completed"

    artifacts = tools.list_artifacts(output_dir=output_dir)
    assert "exports/Unresolved_Threads_Dossier.md" in artifacts

    content = tools.read_artifact(
        output_dir=output_dir,
        relative_path="exports/Unresolved_Threads_Dossier.md",
    )
    assert content.startswith("# Unresolved Threads Dossier")
