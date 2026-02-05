from __future__ import annotations

from typing import Any

from showrunner.agent import tools
from showrunner.agent.langchain_runtime import LangChainRuntime


class DummySession:
    def __init__(self, result: list[dict[str, Any]] | None = None) -> None:
        self.result = result or []
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.calls.append((query, parameters))
        return self.result


def _write_sample_corpus(tmp_path) -> tuple[Any, Any]:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "book1.txt").write_text(
        "\n".join(
            [
                "Arya Stark left Winterfell.",
                "Jon Snow fought at the Wall.",
            ]
        ),
        encoding="utf-8",
    )
    return input_dir, output_dir


def test_query_graph_maps_events_for_entity() -> None:
    session = DummySession(result=[{"event_id": "evt-1"}])
    result = tools.query_graph(
        query="events_for_entity",
        parameters={"entity_id": "entity-1"},
        session=session,
    )

    assert result == [{"event_id": "evt-1"}]
    assert session.calls


def test_langchain_runtime_run_and_list_artifacts(tmp_path) -> None:
    input_dir, output_dir = _write_sample_corpus(tmp_path)
    runtime = LangChainRuntime()

    result = runtime.run(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    artifacts = runtime.list_artifacts(output_dir=output_dir)
    assert "exports/Unresolved_Threads_Dossier.md" in artifacts


def test_langchain_runtime_query_graph_uses_session() -> None:
    session = DummySession(result=[{"event_id": "evt-2"}])
    runtime = LangChainRuntime(graph_session=session)

    result = runtime.query_graph(
        query="events_for_entity",
        parameters={"entity_id": "entity-2"},
    )

    assert result == [{"event_id": "evt-2"}]
    assert session.calls
