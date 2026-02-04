"""Tests for passive git hooks utilities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from showrunner.contracts import Finding, FindingSeverity
from showrunner.hooks import git_hook_handler
from showrunner.hooks.change_detector import filter_corpus_files, normalize_repo_paths
from showrunner.hooks.git_hook_handler import append_review_queue, build_review_items
from showrunner.hooks.incremental_runner import run_incremental


def test_normalize_repo_paths_resolves_relative_paths(tmp_path: Path) -> None:
    repo_root = tmp_path
    paths = ["corpus/book1.txt", "notes/outline.md"]
    normalized = normalize_repo_paths(paths, repo_root)

    assert normalized[0] == repo_root / "corpus/book1.txt"
    assert normalized[1] == repo_root / "notes/outline.md"


def test_filter_corpus_files_limits_to_corpus_and_text_exts(tmp_path: Path) -> None:
    repo_root = tmp_path
    corpus_root = repo_root / "corpus"
    corpus_root.mkdir()

    corpus_txt = corpus_root / "book1.txt"
    corpus_txt.write_text("text")
    corpus_md = corpus_root / "notes.md"
    corpus_md.write_text("text")
    corpus_png = corpus_root / "image.png"
    corpus_png.write_text("binary")

    outside_txt = repo_root / "notes.txt"
    outside_txt.write_text("text")

    paths = [corpus_txt, corpus_md, corpus_png, outside_txt]
    filtered = filter_corpus_files(paths, corpus_root=corpus_root)

    assert corpus_txt in filtered
    assert corpus_md in filtered
    assert corpus_png not in filtered
    assert outside_txt not in filtered


def test_run_incremental_returns_none_when_no_changes(tmp_path: Path) -> None:
    corpus_root = tmp_path / "corpus"
    output_dir = tmp_path / "out"

    result = run_incremental([], corpus_root=corpus_root, output_dir=output_dir)

    assert result is None


def test_build_review_items_maps_contradictions(tmp_path: Path) -> None:
    finding = Finding(
        finding_id="f-1",
        severity=FindingSeverity.WARN,
        category="contradiction",
        message="Potential contradiction found",
        related_ids=["obl_1", "obl_2"],
    )
    items = build_review_items([finding])

    assert len(items) == 1
    assert items[0].category == "potential_contradiction"
    assert items[0].related_ids == ["obl_1", "obl_2"]


def test_append_review_queue_writes_jsonl(tmp_path: Path) -> None:
    queue_path = tmp_path / "review" / "queue.jsonl"
    items = build_review_items(
        [
            Finding(
                finding_id="f-2",
                severity=FindingSeverity.ERROR,
                category="evidence_gate",
                message="Missing evidence",
                related_ids=["obl_9"],
            )
        ],
        created_at=datetime(2026, 2, 3, tzinfo=UTC),
    )

    append_review_queue(items, queue_path)

    lines = queue_path.read_text().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["item_id"] == items[0].item_id
    assert data["status"] == "pending"


def test_run_hook_returns_zero_on_handler_error(tmp_path: Path, monkeypatch) -> None:
    def _boom(_repo_root: Path) -> int:
        raise RuntimeError("boom")

    monkeypatch.setattr(git_hook_handler, "_handle_pre_commit", _boom)

    result = git_hook_handler.run_hook("pre-commit", repo_root=tmp_path)

    assert result == 0
