"""Reveal ledger contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateTruth(BaseModel):
    """A possible answer to a mystery."""

    truth_id: str = Field(..., description="Unique identifier for the candidate truth")
    description: str = Field(..., description="Description of the candidate truth")
    evidence_for: list[str] = Field(
        default_factory=list,
        description="Evidence anchor IDs supporting this truth",
    )
    evidence_against: list[str] = Field(
        default_factory=list,
        description="Evidence anchor IDs contradicting this truth",
    )
    likelihood: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated likelihood (0-1)")

    model_config = {"frozen": True}


def _empty_candidate_truths() -> list[CandidateTruth]:
    return []


class RevealEntry(BaseModel):
    """A mystery with its reveal plan and candidate truths."""

    reveal_id: str = Field(..., description="Unique identifier for this reveal entry")
    mystery_obligation_id: str = Field(..., description="Obligation ID for the underlying mystery")
    mystery_description: str = Field(..., description="Description of the mystery")
    candidate_truths: list[CandidateTruth] = Field(
        default_factory=_empty_candidate_truths,
        description="Candidate truths for this mystery",
    )
    selected_truth: str | None = Field(default=None, description="Chosen truth_id when decided")
    reveal_placement: str | None = Field(
        default=None, description="Suggested placement (book/chapter hint)"
    )
    characters_who_learn: list[str] = Field(
        default_factory=list,
        description="Entity IDs for characters who learn the truth",
    )
    dramatic_impact: str = Field(
        default="moderate", description="Impact label (major/moderate/minor)"
    )

    model_config = {"frozen": True}
