from __future__ import annotations

from showrunner.agent.deepagents_runtime import DeepagentsRuntime


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
