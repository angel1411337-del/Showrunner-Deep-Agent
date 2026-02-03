"""Document and passage contracts for canon indexing."""

from pydantic import BaseModel, Field


class DocumentUnit(BaseModel):
    """Normalized input document from file or folder.

    Represents a single source file normalized to a common structure
    for downstream processing by the canon indexer.
    """

    source_id: str = Field(
        ...,
        description="Unique identifier for this source (e.g., 'book1', 'book1_ch1')",
    )
    source_path: str = Field(
        ...,
        description="Original file path of the source document",
    )
    order_hint: int = Field(
        ...,
        ge=0,
        description="Ordering position within the corpus (0-indexed)",
    )
    raw_text: str = Field(
        ...,
        description="Full raw text content of the document",
    )
    book_label: str | None = Field(
        default=None,
        description="Optional book/volume label if available",
    )
    chapter_label: str | None = Field(
        default=None,
        description="Optional chapter label if available",
    )

    model_config = {"frozen": True}


class PassageRecord(BaseModel):
    """Paragraph-level passage with stable ID for evidence anchoring.

    Passage IDs follow the format: {source_id}:{paragraph_index}
    These IDs remain stable across reruns when text and segmentation rules unchanged.
    """

    passage_id: str = Field(
        ...,
        description="Stable ID in format source_id:paragraph_index",
    )
    source_id: str = Field(
        ...,
        description="Source document this passage belongs to",
    )
    paragraph_index: int = Field(
        ...,
        ge=0,
        description="Zero-indexed paragraph position within source",
    )
    text: str = Field(
        ...,
        description="The passage text content",
    )
    char_start: int = Field(
        ...,
        ge=0,
        description="Character offset start within source document",
    )
    char_end: int = Field(
        ...,
        ge=0,
        description="Character offset end within source document",
    )

    model_config = {"frozen": True}
