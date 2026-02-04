"""Wiki-oriented contracts for events, relationships, and temporal metadata."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class StoryTime(BaseModel):
    """In-world time metadata for an element."""

    time_label: str | None = Field(
        default=None,
        description="Human-readable in-world time label (e.g., '298 AC, late summer')",
    )
    time_start: str | None = Field(
        default=None,
        description="Optional in-world start time (ISO-like string or canon label)",
    )
    time_end: str | None = Field(
        default=None,
        description="Optional in-world end time (ISO-like string or canon label)",
    )

    @model_validator(mode="after")
    def _require_time_info(self) -> "StoryTime":
        if not any([self.time_label, self.time_start, self.time_end]):
            raise ValueError("StoryTime requires at least one of time_label, time_start, time_end.")
        return self

    model_config = {"frozen": True}


class StoryOrder(BaseModel):
    """Narrative order metadata for an element."""

    order_index: int = Field(
        ...,
        ge=0,
        description="Zero-based ordering within the narrative timeline",
    )
    order_label: str | None = Field(
        default=None,
        description="Optional narrative label (e.g., 'book2:3', 'chapter 12')",
    )
    source_id: str | None = Field(
        default=None,
        description="Optional source document ID for the narrative order",
    )
    passage_id: str | None = Field(
        default=None,
        description="Optional passage ID for the narrative order",
    )

    model_config = {"frozen": True}


class EventType(str, Enum):
    """Event classification for wiki entries."""

    BATTLE = "battle"
    DEATH = "death"
    TREATY = "treaty"
    BETRAYAL = "betrayal"
    MARRIAGE = "marriage"
    CORONATION = "coronation"
    TRAVEL = "travel"
    DISCOVERY = "discovery"
    OTHER = "other"


class RelationshipType(str, Enum):
    """Relationship classification between entities."""

    ALLIANCE = "alliance"
    ENMITY = "enmity"
    KINSHIP = "kinship"
    OATH = "oath"
    DEBT = "debt"
    COMMAND = "command"
    MEMBERSHIP = "membership"
    OWNERSHIP = "ownership"
    OTHER = "other"


class Event(BaseModel):
    """Canonical event suitable for a narrative wiki."""

    event_id: str = Field(..., description="Unique identifier for this event")
    event_type: EventType = Field(..., description="Event category")
    title: str = Field(..., description="Short event title")
    description: str = Field(..., description="Event summary")
    participant_entity_ids: list[str] = Field(
        default_factory=list,
        description="Entity IDs participating in the event",
    )
    location_entity_id: str | None = Field(
        default=None,
        description="Primary location entity ID for the event",
    )
    related_obligation_ids: list[str] = Field(
        default_factory=list,
        description="Related obligation IDs (if event resolves or triggers obligations)",
    )
    evidence_anchor_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence anchor IDs supporting this event",
    )
    story_time: StoryTime = Field(..., description="In-world time metadata")
    story_order: StoryOrder = Field(..., description="Narrative order metadata")
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}


class Relationship(BaseModel):
    """Relationship between two entities with provenance and temporal metadata."""

    relationship_id: str = Field(..., description="Unique identifier for this relationship")
    relation_type: RelationshipType = Field(..., description="Relationship category")
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    description: str = Field(..., description="Summary of the relationship")
    evidence_anchor_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence anchor IDs supporting this relationship",
    )
    story_time: StoryTime = Field(..., description="In-world time metadata")
    story_order: StoryOrder = Field(..., description="Narrative order metadata")
    created_at: datetime = Field(..., description="Real-world creation timestamp")

    model_config = {"frozen": True}
