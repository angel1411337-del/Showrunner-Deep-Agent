"""Quality assurance contracts for findings and metrics."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """Severity levels for quality findings."""

    ERROR = "error"  # Hard gate failure
    WARN = "warn"  # Soft warning (MVP: contradictions)
    INFO = "info"  # Informational


class Finding(BaseModel):
    """A quality validation finding.

    Findings capture issues discovered during validation:
    - ERROR: Hard gate violations (e.g., missing evidence)
    - WARN: Soft issues (e.g., contradictions in MVP)
    - INFO: Informational notes
    """

    finding_id: str = Field(
        ...,
        description="Unique identifier for this finding",
    )
    severity: FindingSeverity = Field(
        ...,
        description="Severity level of the finding",
    )
    category: str = Field(
        ...,
        description="Category of finding (e.g., 'evidence_gate', 'schema')",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the finding",
    )
    source_location: str | None = Field(
        default=None,
        description="Location in source files where issue was found",
    )
    related_ids: list[str] = Field(
        default_factory=list,
        description="IDs of related entities/obligations/passages",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this finding was recorded",
    )

    model_config = {"frozen": True}


class MetricsReport(BaseModel):
    """Quality metrics for a pipeline run.

    Tracks all MVP quality metrics:
    - obligations-with-evidence rate (target 100%)
    - ER ambiguity rate
    - obligation dedupe rate
    - runtime/cost per run
    """

    run_id: str = Field(
        ...,
        description="ID of the pipeline run",
    )
    timestamp: datetime = Field(
        ...,
        description="When metrics were collected",
    )
    # Core quality metrics
    obligations_with_evidence_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of obligations with ≥1 evidence anchor",
    )
    er_ambiguity_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of aliases with ambiguous resolution",
    )
    obligation_dedupe_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of obligations identified as duplicates",
    )
    # Counts
    total_passages: int = Field(
        ...,
        ge=0,
        description="Total passages indexed",
    )
    total_entities: int = Field(
        ...,
        ge=0,
        description="Total entities resolved",
    )
    total_obligations: int = Field(
        ...,
        ge=0,
        description="Total obligations extracted",
    )
    # Performance
    runtime_seconds: float = Field(
        ...,
        ge=0.0,
        description="Total pipeline runtime in seconds",
    )
    # Optional V1 metrics
    contradiction_rate: float | None = Field(
        default=None,
        description="V1: contradiction rate per 10k words",
    )

    model_config = {"frozen": True}
