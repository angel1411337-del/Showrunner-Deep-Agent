from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from showrunner.agent import tools
from showrunner.agent.deepagents_runtime import DeepagentsRuntime
from showrunner.agent.langchain_runtime import LangChainRuntime
from showrunner.agent.runtime import AgentRuntime, RuntimeMode, parse_runtime_mode

if TYPE_CHECKING:
    from pathlib import Path


class DummySession:
    def __init__(self, result: list[dict[str, Any]] | None = None) -> None:
        self.result = result or []
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.calls.append((query, parameters))
        return self.result


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


def test_agent_runtime_deepagents_runs_pipeline(tmp_path: Path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(input_dir)

    runtime = AgentRuntime(mode="deepagents")

    result = runtime.run(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    assert (output_dir / "exports" / "Unresolved_Threads_Dossier.md").exists()


def test_agent_runtime_query_graph_langchain() -> None:
    session = DummySession(result=[{"event_id": "evt-1"}])
    runtime = AgentRuntime(
        mode="langchain",
        langchain_runtime=LangChainRuntime(graph_session=session),
    )

    result = runtime.query_graph(query="events_for_entity", parameters={"entity_id": "entity-1"})

    assert result == [{"event_id": "evt-1"}]
    assert session.calls


def test_agent_runtime_query_graph_deepagents() -> None:
    session = DummySession(result=[{"event_id": "evt-2"}])
    runtime = AgentRuntime(
        mode="deepagents",
        deepagents_runtime=DeepagentsRuntime(graph_session=session),
    )

    result = runtime.query_graph(query="events_for_entity", parameters={"entity_id": "entity-2"})

    assert result == [{"event_id": "evt-2"}]
    assert session.calls


def test_agent_runtime_repl_program_deepagents() -> None:
    session = DummySession(result=[{"event_id": "evt-3"}])
    runtime = AgentRuntime(
        mode="deepagents",
        deepagents_runtime=DeepagentsRuntime(graph_session=session),
    )

    result = runtime.run_repl_program(
        prompt="alpha",
        code=(
            "env.emit_tool_call("
            "'query_graph', "
            "query='events_for_entity', "
            "parameters={'entity_id': 'entity-3'}"
            ")"
        ),
    )

    assert result.outputs == [[{"event_id": "evt-3"}]]
    assert session.calls


def test_agent_runtime_repl_program_unsupported() -> None:
    runtime = AgentRuntime(mode="pipeline")

    with pytest.raises(NotImplementedError):
        runtime.run_repl_program(prompt="alpha", code="env.emit_tool_call('noop')")


def test_agent_runtime_unsupported_modes_raise(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        AgentRuntime(mode="unknown")


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
