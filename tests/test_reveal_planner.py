"""Tests for reveal ledger planning."""

from __future__ import annotations

from typing import TYPE_CHECKING

from showrunner.contracts import EvidenceAnchor, Obligation, ObligationCategory
from showrunner.planners.reveal_planner import RevealPlanner

if TYPE_CHECKING:
    from pathlib import Path


def _make_mystery(obligation_id: str, anchor_id: str) -> Obligation:
    return Obligation(
        obligation_id=obligation_id,
        category=ObligationCategory.MYSTERY,
        description="Who hired the faceless assassins?",
        evidence_anchor_ids=[anchor_id],
        last_seen_passage_id="book1:1",
        confidence=0.7,
        related_entity_ids=["entity_01"],
    )


def _make_plot_thread(obligation_id: str, anchor_id: str) -> Obligation:
    return Obligation(
        obligation_id=obligation_id,
        category=ObligationCategory.PLOT_THREAD,
        description="The hero must return home.",
        evidence_anchor_ids=[anchor_id],
        last_seen_passage_id="book1:2",
        confidence=0.6,
        related_entity_ids=["entity_02"],
    )


def test_plan_returns_empty_for_no_obligations() -> None:
    planner = RevealPlanner()
    assert planner.plan([], []) == []


def test_plan_filters_only_mysteries() -> None:
    planner = RevealPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_001",
            passage_id="book1:1",
            char_start=0,
            char_end=10,
            excerpt="Who hired",
        )
    ]
    mystery = _make_mystery("obl_001", "anc_001")
    plot_thread = _make_plot_thread("obl_002", "anc_001")

    entries = planner.plan([plot_thread, mystery], anchors)
    assert len(entries) == 1
    assert entries[0].mystery_obligation_id == mystery.obligation_id


def test_plan_populates_candidate_truths_from_evidence() -> None:
    planner = RevealPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_010",
            passage_id="book1:3",
            char_start=5,
            char_end=20,
            excerpt="faceless",
        )
    ]
    mystery = _make_mystery("obl_010", "anc_010")

    entries = planner.plan([mystery], anchors)
    assert entries
    candidate = entries[0].candidate_truths[0]
    assert candidate.evidence_for == mystery.evidence_anchor_ids


def test_render_csv_includes_headers_and_row(tmp_path: Path) -> None:
    planner = RevealPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_020",
            passage_id="book1:4",
            char_start=2,
            char_end=12,
            excerpt="mystery",
        )
    ]
    mystery = _make_mystery("obl_020", "anc_020")
    entries = planner.plan([mystery], anchors)

    csv_text = planner.render_csv(entries)
    lines = csv_text.strip().splitlines()
    assert lines
    assert lines[0].startswith("reveal_id,")
    assert "mystery_obligation_id" in lines[0]
    assert entries[0].reveal_id in lines[1]

    out_path = tmp_path / "mysteries_reveals_table.csv"
    planner.export_csv(entries, out_path)
    assert out_path.exists()
