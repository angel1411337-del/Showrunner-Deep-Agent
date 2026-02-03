"""Tests for twist bank planning."""

from __future__ import annotations

from showrunner.contracts import EvidenceAnchor, Obligation, ObligationCategory
from showrunner.planners.twist_planner import TwistPlanner


def _make_obligation(obligation_id: str, anchor_id: str) -> Obligation:
    return Obligation(
        obligation_id=obligation_id,
        category=ObligationCategory.PLOT_THREAD,
        description="The hero must reclaim the throne.",
        evidence_anchor_ids=[anchor_id],
        last_seen_passage_id="book1:1",
        confidence=0.7,
        related_entity_ids=["entity_01"],
    )


def test_plan_returns_empty_for_no_obligations() -> None:
    planner = TwistPlanner()
    assert planner.plan([], []) == []


def test_plan_creates_twist_for_obligation() -> None:
    planner = TwistPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_001",
            passage_id="book1:1",
            char_start=0,
            char_end=10,
            excerpt="hero",
        )
    ]
    obligation = _make_obligation("obl_001", "anc_001")

    twists = planner.plan([obligation], anchors)
    assert len(twists) == 1
    twist = twists[0]
    assert obligation.obligation_id in twist.affected_obligations
    assert twist.evidence_support == obligation.evidence_anchor_ids
    assert twist.affected_entities == obligation.related_entity_ids


def test_render_markdown_includes_header_and_twist() -> None:
    planner = TwistPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_002",
            passage_id="book1:2",
            char_start=0,
            char_end=10,
            excerpt="throne",
        )
    ]
    obligation = _make_obligation("obl_002", "anc_002")
    twists = planner.plan([obligation], anchors)

    markdown = planner.render_markdown(twists)
    assert markdown.startswith("# Twist Bank")
    assert twists[0].twist_id in markdown


def test_export_markdown_writes_file(tmp_path) -> None:
    planner = TwistPlanner()
    anchors = [
        EvidenceAnchor(
            anchor_id="anc_003",
            passage_id="book1:3",
            char_start=0,
            char_end=10,
            excerpt="betrayal",
        )
    ]
    obligation = _make_obligation("obl_003", "anc_003")
    twists = planner.plan([obligation], anchors)

    out_path = tmp_path / "twist_bank.md"
    planner.export_markdown(twists, out_path)
    assert out_path.exists()
