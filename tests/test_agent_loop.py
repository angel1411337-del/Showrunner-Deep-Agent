from pathlib import Path

from showrunner.agent.loop import AgentLoop


def _write_sample_corpus(corpus_root: Path) -> None:
    corpus_root.mkdir(parents=True, exist_ok=True)
    (corpus_root / "chapter1.txt").write_text(
        "Jon Snow swore an oath. The Wall loomed over Winterfell.",
        encoding="utf-8",
    )


def test_agent_loop_runs_and_writes_report(tmp_path: Path):
    corpus_root = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(corpus_root)

    loop = AgentLoop()
    result = loop.run(input_source=corpus_root, output_dir=output_dir)

    assert result.status == "completed"
    assert result.report_path is not None
    assert result.report_path.exists()
    assert (output_dir / "qa" / "agent_loop.json").exists()
    assert any(step.name == "plan" for step in result.steps)
    assert any(step.name == "propose" for step in result.steps)
    assert any(step.name == "validate" for step in result.steps)
    assert any(step.name == "persist" for step in result.steps)


def test_agent_loop_fails_when_schema_dir_missing(tmp_path: Path):
    corpus_root = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(corpus_root)

    loop = AgentLoop(schema_dir=tmp_path / "missing_schemas")
    result = loop.run(input_source=corpus_root, output_dir=output_dir)

    assert result.status == "failed"
    assert result.findings
    assert any(f.category == "schema" for f in result.findings)
