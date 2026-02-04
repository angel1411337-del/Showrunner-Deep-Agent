"""Entry point for passive git hooks."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

from showrunner.contracts import Finding, FindingSeverity, ReviewQueueItem
from showrunner.hooks.change_detector import detect_changed_text_files
from showrunner.hooks.incremental_runner import (
    resolve_corpus_root,
    resolve_output_dir,
    run_incremental,
)

ReviewCategory = Literal[
    "ambiguous_entity",
    "low_confidence_obligation",
    "potential_contradiction",
]
ReviewSeverity = Literal["high", "medium", "low"]


def _load_findings(findings_path: Path) -> list[Finding]:
    if not findings_path.exists():
        return []
    findings: list[Finding] = []
    for line in findings_path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        findings.append(Finding.model_validate(data))
    return findings


def build_review_items(
    findings: Iterable[Finding],
    *,
    created_at: datetime | None = None,
) -> list[ReviewQueueItem]:
    timestamp = created_at or datetime.now(tz=UTC)
    items: list[ReviewQueueItem] = []
    for finding in findings:
        category_map: dict[str, ReviewCategory] = {
            "contradiction": "potential_contradiction",
            "alias": "ambiguous_entity",
            "entity_resolution": "ambiguous_entity",
            "er_ambiguity": "ambiguous_entity",
            "evidence_gate": "low_confidence_obligation",
            "schema": "low_confidence_obligation",
            "referential_integrity": "low_confidence_obligation",
        }
        category: ReviewCategory = category_map.get(
            finding.category,
            "low_confidence_obligation",
        )
        severity_map: dict[FindingSeverity, ReviewSeverity] = {
            FindingSeverity.ERROR: "high",
            FindingSeverity.WARN: "medium",
            FindingSeverity.INFO: "low",
        }
        severity: ReviewSeverity = severity_map.get(finding.severity, "medium")

        items.append(
            ReviewQueueItem(
                item_id=f"review_{uuid4().hex[:8]}",
                created_at=timestamp,
                category=category,
                severity=severity,
                description=finding.message,
                related_ids=list(finding.related_ids or []),
                suggested_actions=["Review the evidence and confirm or dismiss the issue."],
                status="pending",
            )
        )
    return items


def append_review_queue(items: Iterable[ReviewQueueItem], queue_path: Path) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item.model_dump(), default=str) + "\n")


def _handle_pre_commit(repo_root: Path) -> int:
    corpus_root = resolve_corpus_root(repo_root)
    output_dir = resolve_output_dir(repo_root)
    changed_files = detect_changed_text_files(repo_root, corpus_root=corpus_root, staged=True)
    state = run_incremental(changed_files, corpus_root=corpus_root, output_dir=output_dir)
    if state and state.get("findings"):
        items = build_review_items(state.get("findings", []))
        queue_path = repo_root / "review" / "queue.jsonl"
        append_review_queue(items, queue_path)
    return 0


def _handle_post_commit(repo_root: Path) -> int:
    output_dir = resolve_output_dir(repo_root)
    findings_path = output_dir / "qa" / "findings.jsonl"
    findings = _load_findings(findings_path)
    if not findings:
        corpus_root = resolve_corpus_root(repo_root)
        changed_files = detect_changed_text_files(
            repo_root,
            corpus_root=corpus_root,
            base="HEAD~1",
            head="HEAD",
            staged=False,
        )
        state = run_incremental(changed_files, corpus_root=corpus_root, output_dir=output_dir)
        if state:
            findings = list(state.get("findings", []))

    if findings:
        items = build_review_items(findings)
        queue_path = repo_root / "review" / "queue.jsonl"
        append_review_queue(items, queue_path)
    return 0


def run_hook(hook: str, *, repo_root: Path) -> int:
    def _safe_execute(handler: Callable[[Path], int]) -> int:
        try:
            return handler(repo_root)
        except Exception as exc:  # pragma: no cover - safety net for hook execution
            print(f"[showrunner hooks] warning: {exc}")
            return 0

    if hook == "pre-commit":
        return _safe_execute(_handle_pre_commit)
    if hook == "post-commit":
        return _safe_execute(_handle_post_commit)
    raise ValueError(f"Unsupported hook type: {hook}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Showrunner passive hook handler.")
    parser.add_argument("--hook", choices=["pre-commit", "post-commit"], required=True)
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    return run_hook(args.hook, repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
