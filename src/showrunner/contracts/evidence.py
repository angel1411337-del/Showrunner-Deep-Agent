"""Evidence anchor contracts for provenance tracking."""

from pydantic import BaseModel, Field


class EvidenceAnchor(BaseModel):
    """An evidence anchor pointing to a specific text span.

    Anchors provide provenance for claims, linking obligations and entities
    back to their source passages with exact character positions.
    """

    anchor_id: str = Field(
        ...,
        description="Unique identifier for this evidence anchor",
    )
    passage_id: str = Field(
        ...,
        description="The passage this anchor references (source_id:paragraph_index)",
    )
    char_start: int = Field(
        ...,
        ge=0,
        description="Character offset start within passage",
    )
    char_end: int = Field(
        ...,
        ge=0,
        description="Character offset end within passage",
    )
    excerpt: str = Field(
        ...,
        min_length=1,
        description="Extracted text excerpt for quick reference",
    )

    model_config = {"frozen": True}


class EvidenceIndex(BaseModel):
    """Index linking evidence anchors to entities or obligations.

    Groups multiple evidence anchors that support a single claim,
    enabling efficient lookup and integrity validation.
    """

    index_id: str = Field(
        ...,
        description="Unique identifier for this index entry",
    )
    target_type: str = Field(
        ...,
        pattern="^(entity|obligation)$",
        description="Type of target: 'entity' or 'obligation'",
    )
    target_id: str = Field(
        ...,
        description="ID of the entity or obligation this evidence supports",
    )
    anchor_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of evidence anchor IDs supporting this target",
    )

    model_config = {"frozen": True}
