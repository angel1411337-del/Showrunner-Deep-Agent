"""Outline planning contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Beat(BaseModel):
    """A story beat in the outline."""

    beat_id: str = Field(..., description="Unique identifier for this beat")
    description: str = Field(..., description="Human-readable beat description")
    chapter_hint: str | None = Field(default=None, description="Optional chapter placement hint")
    pov_character: str | None = Field(
        default=None, description="Optional POV character for the beat"
    )
    obligations_addressed: list[str] = Field(
        default_factory=list, description="Obligation IDs addressed in this beat"
    )
    entities_involved: list[str] = Field(
        default_factory=list, description="Entity IDs involved in this beat"
    )
    is_bridging: bool = Field(
        default=False, description="Whether this beat bridges convergence points"
    )

    model_config = {"frozen": True}


class ConvergencePoint(BaseModel):
    """Where multiple plot threads converge."""

    convergence_id: str = Field(..., description="Unique identifier for convergence")
    description: str = Field(..., description="Description of the convergence")
    converging_obligations: list[str] = Field(
        default_factory=list, description="Obligation IDs converging here"
    )
    suggested_placement: str = Field(..., description="Suggested placement (book/chapter hint)")
    dramatic_weight: float = Field(
        ..., ge=0.0, le=1.0, description="Relative dramatic weight (0-1)"
    )

    model_config = {"frozen": True}


def _empty_beats() -> list[Beat]:
    return []


def _empty_convergences() -> list[ConvergencePoint]:
    return []


class OutlineSection(BaseModel):
    """A section of the master outline."""

    section_id: str = Field(..., description="Unique identifier for section")
    title: str = Field(..., description="Section title")
    book_number: int = Field(..., ge=1, description="Book number for this section")
    beats: list[Beat] = Field(default_factory=_empty_beats, description="Beats in this section")
    convergence_points: list[ConvergencePoint] = Field(
        default_factory=_empty_convergences,
        description="Convergence points in this section",
    )

    model_config = {"frozen": True}
