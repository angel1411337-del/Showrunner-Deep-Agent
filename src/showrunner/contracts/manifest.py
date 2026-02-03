"""Run and dataset manifest contracts for reproducibility."""

from datetime import datetime

from pydantic import BaseModel, Field


class RunManifest(BaseModel):
    """Manifest capturing all metadata for a pipeline run.

    Enables reproducibility by tracking git SHA, versions, hashes,
    and configuration for each run.
    """

    run_id: str = Field(
        ...,
        description="Unique identifier for this run",
    )
    timestamp: datetime = Field(
        ...,
        description="When the run started",
    )
    git_sha: str = Field(
        ...,
        description="Git commit SHA of the codebase",
    )
    python_version: str = Field(
        ...,
        description="Python version used (e.g., '3.14.2')",
    )
    segmentation_version: str = Field(
        ...,
        description="Version of segmentation rules used",
    )
    config_hash: str = Field(
        ...,
        description="Hash of the configuration used",
    )
    input_dataset_hash: str = Field(
        ...,
        description="Hash of the input dataset",
    )
    lockfile_hash: str | None = Field(
        default=None,
        description="Hash of uv.lock for dependency reproducibility",
    )
    completed_timestamp: datetime | None = Field(
        default=None,
        description="When the run completed (None if still running)",
    )
    status: str = Field(
        default="running",
        pattern="^(running|completed|failed)$",
        description="Current run status",
    )

    model_config = {"frozen": True}


class DatasetManifest(BaseModel):
    """Manifest describing the input dataset.

    Enumerates all source files and provides aggregate statistics
    for validation and reproducibility.
    """

    manifest_id: str = Field(
        ...,
        description="Unique identifier for this manifest",
    )
    total_documents: int = Field(
        ...,
        ge=0,
        description="Total number of input documents",
    )
    total_characters: int = Field(
        ...,
        ge=0,
        description="Total character count across all documents",
    )
    source_files: list[str] = Field(
        ...,
        description="List of source file paths",
    )
    content_hash: str = Field(
        ...,
        description="Hash of concatenated content for integrity",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this manifest was created",
    )

    model_config = {"frozen": True}
