"""Entity resolution contracts."""

from enum import Enum

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities recognized by ER v1.

    MVP targets: people, places, groups, titles, artifacts, vehicles (limited).
    """

    PERSON = "person"
    PLACE = "place"
    GROUP = "group"
    TITLE = "title"
    ARTIFACT = "artifact"
    VEHICLE = "vehicle"


class Entity(BaseModel):
    """A resolved canonical entity.

    Entities are deduplicated, canonical representations of named items
    in the corpus. Each entity has a type and tracks first appearance
    and mention frequency.
    """

    entity_id: str = Field(
        ...,
        description="Unique identifier for this entity",
    )
    canonical_name: str = Field(
        ...,
        description="The canonical/preferred name for this entity",
    )
    entity_type: EntityType = Field(
        ...,
        description="Classification of entity type",
    )
    first_seen_passage: str = Field(
        ...,
        description="Passage ID where entity first appears",
    )
    mention_count: int = Field(
        ...,
        ge=1,
        description="Total number of mentions across corpus",
    )
    is_important: bool = Field(
        default=False,
        description="Flag for entities marked as important (esp. vehicles)",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the entity",
    )

    model_config = {"frozen": True}


class AliasEntry(BaseModel):
    """Mapping from alias/variant name to canonical entity.

    Tracks all the different ways an entity can be referred to,
    with confidence scores for fuzzy matches.
    """

    alias_id: str = Field(
        ...,
        description="Unique identifier for this alias entry",
    )
    alias_text: str = Field(
        ...,
        description="The alias/variant text that maps to an entity",
    )
    entity_id: str = Field(
        ...,
        description="The canonical entity this alias resolves to",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this alias mapping (0-1)",
    )

    model_config = {"frozen": True}


class OverrideAction(str, Enum):
    """Actions available for human override rules."""

    ASSIGN = "assign"  # Force alias to specific entity
    SPLIT = "split"  # Split entity into multiple
    MERGE = "merge"  # Merge multiple entities
    IGNORE = "ignore"  # Ignore this alias entirely


class OverrideRule(BaseModel):
    """Human override rule for entity resolution.

    Implements 'human wins' policy - manual corrections take precedence
    over automated entity resolution.
    """

    override_id: str = Field(
        ...,
        description="Unique identifier for this override rule",
    )
    target_alias: str = Field(
        ...,
        description="The alias text this rule applies to",
    )
    action: OverrideAction = Field(
        ...,
        description="The action to take for this override",
    )
    target_entity_id: str | None = Field(
        default=None,
        description="Entity ID to assign (for ASSIGN action)",
    )
    reason: str = Field(
        ...,
        description="Human-provided reason for this override",
    )

    model_config = {"frozen": True}
