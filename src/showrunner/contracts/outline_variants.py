"""Contracts for multi-outline variants with payoffs and inflection points."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, Field

from showrunner.contracts.wiki import StoryOrder, StoryTime  # noqa: TC001


def _empty_payoffs() -> list[Payoff]:
    return []


def _empty_inflections() -> list[InflectionPoint]:
    return []


class Payoff(BaseModel):
    """A proposed resolution path for an unresolved thread."""

    payoff_id: str = Field(..., description="Unique payoff identifier")
    obligation_id: str = Field(..., description="Obligation this payoff resolves")
    title: str = Field(..., description="Short payoff label")
    description: str = Field(..., description="Payoff description")
    evidence_anchor_ids: list[str] = Field(
        ..., min_length=1, description="Evidence anchors supporting this payoff path"
    )
    story_time: StoryTime = Field(..., description="In-world time for payoff")
    story_order: StoryOrder = Field(..., description="Narrative order for payoff")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}


class InflectionOption(BaseModel):
    """One possible direction at an inflection point."""

    option_id: str = Field(..., description="Unique option identifier")
    title: str = Field(..., description="Short option title")
    description: str = Field(..., description="What this option changes")
    payoff_ids: list[str] = Field(
        default_factory=list,
        description="Payoffs enabled or affected by this option",
    )
    evidence_anchor_ids: list[str] = Field(
        ..., min_length=1, description="Evidence anchors supporting this option"
    )
    risk_notes: list[str] = Field(default_factory=list, description="Continuity or thematic risks")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    model_config = {"frozen": True}


class InflectionPoint(BaseModel):
    """A decision node where the story can fork without breaking canon."""

    inflection_id: str = Field(..., description="Unique inflection identifier")
    title: str = Field(..., description="Short label for the decision node")
    description: str = Field(..., description="Why this is a branch point")
    evidence_anchor_ids: list[str] = Field(
        ..., min_length=1, description="Evidence anchors supporting the inflection"
    )
    story_time: StoryTime = Field(..., description="In-world time for the inflection")
    story_order: StoryOrder = Field(..., description="Narrative order for the inflection")
    options: list[InflectionOption] = Field(..., min_length=1)
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}


class OutlineBeat(BaseModel):
    """A beat in an outline variant."""

    beat_id: str = Field(..., description="Unique beat identifier")
    title: str = Field(..., description="Short beat title")
    description: str = Field(..., description="Beat description")
    obligation_ids: list[str] = Field(default_factory=list)
    payoff_ids: list[str] = Field(default_factory=list)
    evidence_anchor_ids: list[str] = Field(..., min_length=1)
    story_time: StoryTime = Field(..., description="In-world time for beat")
    story_order: StoryOrder = Field(..., description="Narrative order for beat")

    model_config = {"frozen": True}


class OutlineVariant(BaseModel):
    """A full outline option constrained by canon and evidence."""

    outline_id: str = Field(..., description="Unique outline identifier")
    title: str = Field(..., description="Short outline title")
    strategy: Literal["conservative", "balanced", "high_risk"] = Field(
        ..., description="Tone of the outline approach"
    )
    summary: str = Field(..., description="High-level outline summary")
    beats: list[OutlineBeat] = Field(..., min_length=1)
    payoff_ids: list[str] = Field(default_factory=list)
    inflection_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}


class MultiOutlinePack(BaseModel):
    """Container for multiple outline variants plus payoffs and inflections."""

    pack_id: str = Field(..., description="Unique pack identifier")
    corpus_label: str = Field(..., description="Corpus label or run identifier")
    outlines: list[OutlineVariant] = Field(..., min_length=1)
    payoffs: list[Payoff] = Field(default_factory=_empty_payoffs)
    inflections: list[InflectionPoint] = Field(default_factory=_empty_inflections)
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}
