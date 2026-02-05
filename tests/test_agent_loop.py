from __future__ import annotations

from typing import TYPE_CHECKING

from showrunner.agent.loop import AgentLoop

if TYPE_CHECKING:
    from pathlib import Path


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
    plan_step = _get_step(result.steps, "plan")
    propose_step = _get_step(result.steps, "propose")
    validate_step = _get_step(result.steps, "validate")
    repair_step = _get_step(result.steps, "repair")
    _get_step(result.steps, "persist")

    assert plan_step.details.get("required_artifacts")
    assert propose_step.status == "completed"
    assert validate_step.details.get("missing_artifacts") == []
    assert validate_step.details.get("schema_errors") == 0
    assert repair_step.status == "skipped"


def test_agent_loop_fails_when_schema_dir_missing(tmp_path: Path):
    corpus_root = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    _write_sample_corpus(corpus_root)

    loop = AgentLoop(schema_dir=tmp_path / "missing_schemas")
    result = loop.run(input_source=corpus_root, output_dir=output_dir)

    assert result.status == "failed"
    assert result.findings
    assert any(f.category == "schema" for f in result.findings)
    repair_step = _get_step(result.steps, "repair")
    assert repair_step.status == "completed"
    assert repair_step.details.get("queued_items", 0) > 0
    assert (output_dir / "review" / "queue.jsonl").exists()


def _get_step(steps: list[object], name: str):
    for step in steps:
        if getattr(step, "name", None) == name:
            return step
    raise AssertionError(f"Missing step: {name}")
