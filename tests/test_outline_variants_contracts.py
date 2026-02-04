"""Tests for multi-outline variant contracts (payoffs and inflection points)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from showrunner.contracts import StoryOrder, StoryTime
from showrunner.contracts.outline_variants import (
    InflectionOption,
    InflectionPoint,
    MultiOutlinePack,
    OutlineBeat,
    OutlineVariant,
    Payoff,
)


def test_payoff_requires_evidence_and_time_fields() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    story_time = StoryTime(time_label="298 AC", time_start=None, time_end=None)
    story_order = StoryOrder(order_index=4, order_label="book6:1", passage_id="book6:1")

    payoff = Payoff(
        payoff_id="payoff_001",
        obligation_id="obl_001",
        title="Prophecy Fulfilled",
        description="The promised figure is revealed through action.",
        evidence_anchor_ids=["anc_001"],
        story_time=story_time,
        story_order=story_order,
        confidence=0.7,
        created_at=now,
    )

    assert payoff.evidence_anchor_ids == ["anc_001"]
    assert payoff.story_time.time_label == "298 AC"

    with pytest.raises(ValidationError):
        Payoff(
            payoff_id="payoff_002",
            obligation_id="obl_001",
            title="Missing Evidence",
            description="No anchors provided.",
            evidence_anchor_ids=[],
            story_time=story_time,
            story_order=story_order,
            confidence=0.4,
            created_at=now,
        )


def test_inflection_point_requires_options_and_anchors() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    story_time = StoryTime(time_label="299 AC", time_start=None, time_end=None)
    story_order = StoryOrder(order_index=10, order_label="book6:3", passage_id="book6:3")

    option = InflectionOption(
        option_id="opt_001",
        title="Hold the Pact",
        description="Leaders reaffirm alliance despite pressure.",
        payoff_ids=["payoff_001"],
        evidence_anchor_ids=["anc_010"],
        risk_notes=["May delay internal conflict resolution."],
        confidence=0.6,
    )

    point = InflectionPoint(
        inflection_id="infl_001",
        title="Alliance Fractures",
        description="Decision point for coalition response.",
        evidence_anchor_ids=["anc_010"],
        story_time=story_time,
        story_order=story_order,
        options=[option],
        created_at=now,
    )

    assert point.options[0].option_id == "opt_001"

    with pytest.raises(ValidationError):
        InflectionPoint(
            inflection_id="infl_002",
            title="No Options",
            description="Missing options.",
            evidence_anchor_ids=["anc_010"],
            story_time=story_time,
            story_order=story_order,
            options=[],
            created_at=now,
        )


def test_outline_variant_requires_strategy_and_beats() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    story_time = StoryTime(time_label="300 AC", time_start=None, time_end=None)
    story_order = StoryOrder(order_index=1, order_label="book6:0", passage_id="book6:0")

    beat = OutlineBeat(
        beat_id="beat_001",
        title="The Pact Holds",
        description="Alliance solidifies around shared enemy.",
        obligation_ids=["obl_001"],
        payoff_ids=["payoff_001"],
        evidence_anchor_ids=["anc_020"],
        story_time=story_time,
        story_order=story_order,
    )

    outline = OutlineVariant(
        outline_id="outline_001",
        title="Conservative Resolution",
        strategy="conservative",
        summary="Resolves core prophecies with minimal upheaval.",
        beats=[beat],
        payoff_ids=["payoff_001"],
        inflection_ids=["infl_001"],
        confidence=0.8,
        created_at=now,
    )

    assert outline.strategy == "conservative"
    assert outline.beats[0].beat_id == "beat_001"

    with pytest.raises(ValidationError):
        OutlineVariant(
            outline_id="outline_002",
            title="Invalid Strategy",
            strategy="chaotic",
            summary="Invalid strategy value.",
            beats=[beat],
            payoff_ids=[],
            inflection_ids=[],
            confidence=0.2,
            created_at=now,
        )


def test_multi_outline_pack_requires_outlines() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    outline = OutlineVariant(
        outline_id="outline_001",
        title="Balanced Plan",
        strategy="balanced",
        summary="Balances payoff and risk.",
        beats=[
            OutlineBeat(
                beat_id="beat_001",
                title="Opening Move",
                description="Set the board.",
                obligation_ids=[],
                payoff_ids=[],
                evidence_anchor_ids=["anc_030"],
                story_time=StoryTime(time_label="301 AC", time_start=None, time_end=None),
                story_order=StoryOrder(order_index=2, order_label="book6:1", passage_id="book6:1"),
            )
        ],
        payoff_ids=[],
        inflection_ids=[],
        confidence=0.55,
        created_at=now,
    )

    pack = MultiOutlinePack(
        pack_id="pack_001",
        corpus_label="asoiaf_full",
        outlines=[outline],
        payoffs=[],
        inflections=[],
        created_at=now,
    )

    assert pack.outlines[0].outline_id == "outline_001"

    with pytest.raises(ValidationError):
        MultiOutlinePack(
            pack_id="pack_002",
            corpus_label="asoiaf_full",
            outlines=[],
            payoffs=[],
            inflections=[],
            created_at=now,
        )
