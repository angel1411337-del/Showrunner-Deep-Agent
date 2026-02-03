"""Obligation extraction contracts."""

from enum import Enum

from pydantic import BaseModel, Field


class ObligationCategory(str, Enum):
    """Categories of narrative obligations.

    MVP categories: plot threads, Chekhov's guns, prophecies/visions, mysteries.
    """

    PLOT_THREAD = "plot_thread"
    CHEKHOV_GUN = "chekhov_gun"
    PROPHECY_VISION = "prophecy_vision"
    MYSTERY = "mystery"


class Obligation(BaseModel):
    """An unresolved narrative obligation requiring future resolution.

    Obligations are extracted claims/threads from the text that the
    story has implicitly promised to resolve. Each must have at least
    one evidence anchor for provenance.
    """

    obligation_id: str = Field(
        ...,
        description="Unique identifier for this obligation",
    )
    category: ObligationCategory = Field(
        ...,
        description="Classification of obligation type",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the obligation",
    )
    evidence_anchor_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence anchors supporting this obligation (≥1 required)",
    )
    last_seen_passage_id: str = Field(
        ...,
        description="Most recent passage where this obligation was referenced",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this extraction (0-1)",
    )
    is_resolved: bool = Field(
        default=False,
        description="Whether this obligation has been marked as resolved",
    )
    resolution_passage_id: str | None = Field(
        default=None,
        description="Passage where resolution occurred (if resolved)",
    )
    related_entity_ids: list[str] = Field(
        default_factory=list,
        description="Entity IDs related to this obligation",
    )

    model_config = {"frozen": True}


class EdgeType(str, Enum):
    """Types of relationships between obligations."""

    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    DUPLICATES = "duplicates"


class ObligationGraphEdge(BaseModel):
    """Edge connecting two obligations in the obligation graph.

    Represents relationships between obligations for reasoning
    about dependencies, contradictions, and duplicates.
    """

    edge_id: str = Field(
        ...,
        description="Unique identifier for this edge",
    )
    source_obligation_id: str = Field(
        ...,
        description="Source obligation in the relationship",
    )
    target_obligation_id: str = Field(
        ...,
        description="Target obligation in the relationship",
    )
    edge_type: EdgeType = Field(
        ...,
        description="Type of relationship between obligations",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Relationship strength/confidence (0-1)",
    )

    model_config = {"frozen": True}
