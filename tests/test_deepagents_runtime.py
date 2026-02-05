from __future__ import annotations

from showrunner.agent.deepagents_runtime import DeepagentsRuntime


class DummySession:
    def __init__(self, result=None) -> None:
        self.result = result or []
        self.calls = []

    def run(self, query: str, parameters: dict | None = None):
        self.calls.append((query, parameters))
        return self.result


def _write_sample_corpus(tmp_path):
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "book1.txt").write_text(
        "\n".join(
            [
                "Daenerys Targaryen crossed the sea.",
                "Tyrion Lannister learned a secret.",
            ]
        ),
        encoding="utf-8",
    )
    return input_dir, output_dir


def test_deepagents_runtime_run_and_list_artifacts(tmp_path) -> None:
    input_dir, output_dir = _write_sample_corpus(tmp_path)
    runtime = DeepagentsRuntime()

    result = runtime.run(input_source=input_dir, output_dir=output_dir)

    assert result.status == "completed"
    artifacts = runtime.list_artifacts(output_dir=output_dir)
    assert "exports/Unresolved_Threads_Dossier.md" in artifacts


def test_deepagents_runtime_runs_repl_program() -> None:
    session = DummySession(result=[{"event_id": "evt-1"}])
    runtime = DeepagentsRuntime(graph_session=session)

    result = runtime.run_repl_program(
        prompt="alpha",
        code="env.emit_tool_call('query_graph', query='events_for_entity', parameters={'entity_id': 'e1'})",
    )

    assert result.outputs == [[{"event_id": "evt-1"}]]
    assert session.calls
