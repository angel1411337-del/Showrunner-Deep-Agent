"""Review queue contract for passive mode hooks."""

from datetime import datetime  # noqa: TCH003 - used by Pydantic type resolution
from typing import Literal

from pydantic import BaseModel, Field


class ReviewQueueItem(BaseModel):
    """An item requiring human review."""

    item_id: str = Field(..., description="Unique queue item identifier")
    created_at: datetime = Field(..., description="Timestamp when item was queued")
    category: Literal[
        "ambiguous_entity",
        "low_confidence_obligation",
        "potential_contradiction",
    ] = Field(..., description="Queue classification")
    severity: Literal["high", "medium", "low"] = Field(
        ..., description="UX-friendly severity level"
    )
    description: str = Field(..., description="Summary of the issue")
    related_ids: list[str] = Field(
        default_factory=list, description="Related entity/obligation IDs"
    )
    suggested_actions: list[str] = Field(
        default_factory=list, description="Suggested human actions for review"
    )
    status: Literal["pending", "reviewed", "dismissed"] = Field(
        default="pending", description="Review status"
    )
