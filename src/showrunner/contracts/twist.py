"""Twist bank contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TwistProposal(BaseModel):
    """A proposed narrative twist."""

    twist_id: str = Field(..., description="Unique identifier for this twist")
    description: str = Field(..., description="Twist description")
    twist_type: str = Field(..., description="Twist type label")
    affected_obligations: list[str] = Field(
        default_factory=list, description="Obligation IDs affected by this twist"
    )
    affected_entities: list[str] = Field(
        default_factory=list, description="Entity IDs impacted by the twist"
    )
    evidence_support: list[str] = Field(
        default_factory=list, description="Evidence anchors supporting the twist"
    )
    contradictions: list[str] = Field(
        default_factory=list, description="Evidence anchors contradicting the twist"
    )
    required_setup: list[str] = Field(
        default_factory=list, description="Setup beats required before the twist"
    )
    backfill_suggestions: list[str] = Field(
        default_factory=list, description="Suggested backfill for retroactive setup"
    )
    reader_predictability: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Predictability (0-1)"
    )
    thematic_alignment: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Thematic alignment (0-1)"
    )
    risk_notes: list[str] = Field(default_factory=list, description="Risk notes for this twist")

    model_config = {"frozen": True}
