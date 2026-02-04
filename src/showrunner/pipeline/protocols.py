"""Protocol definitions for pipeline components.

Enables dependency injection and testing with mock components.
All components implement these protocols for type safety.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from showrunner.contracts import (
        AliasEntry,
        DocumentUnit,
        Entity,
        Event,
        EvidenceAnchor,
        Finding,
        Obligation,
        ObligationGraphEdge,
        OverrideRule,
        PassageRecord,
        Relationship,
    )


@runtime_checkable
class InputAdapterProtocol(Protocol):
    """Protocol for input adapters that load documents."""

    def load(self, source: Path) -> list[DocumentUnit]:
        """Load and normalize input to DocumentUnits.

        Args:
            source: Path to file or folder

        Returns:
            List of normalized DocumentUnit objects
        """
        ...

    def load_files(self, files: list[Path]) -> list[DocumentUnit]:
        """Load and normalize a specific list of files.

        Args:
            files: Explicit list of files to load

        Returns:
            List of normalized DocumentUnit objects
        """
        ...


@runtime_checkable
class CanonIndexerProtocol(Protocol):
    """Protocol for canon indexers that segment and index passages."""

    @property
    def segmentation_version(self) -> str:
        """Get the segmentation version string."""
        ...

    def segment_paragraphs(self, doc: DocumentUnit) -> list[PassageRecord]:
        """Split document into paragraph-level passages.

        Args:
            doc: Document to segment

        Returns:
            List of PassageRecord objects
        """
        ...

    def index(
        self, docs: list[DocumentUnit], db_path: Path
    ) -> tuple[list[PassageRecord], sqlite3.Connection]:
        """Index all documents and build SQLite lookup.

        Args:
            docs: Documents to index
            db_path: Path for SQLite database

        Returns:
            Tuple of (all_passages, db_connection)
        """
        ...

    def write_passages_jsonl(self, passages: list[PassageRecord], output_path: Path) -> None:
        """Write passages to JSONL file.

        Args:
            passages: Passages to write
            output_path: Path for output file
        """
        ...


@runtime_checkable
class EntityResolverProtocol(Protocol):
    """Protocol for entity resolvers that extract and link entities."""

    @property
    def vehicle_min_mentions(self) -> int:
        """Get minimum mentions threshold for vehicles."""
        ...

    def add_override(self, override: OverrideRule) -> None:
        """Register a human override rule.

        Args:
            override: Override rule to add
        """
        ...

    def extract_entities(self, passages: list[PassageRecord]) -> list[Entity]:
        """Extract entities from passages.

        Args:
            passages: Passages to analyze

        Returns:
            List of extracted Entity objects
        """
        ...

    def build_alias_table(
        self, entities: list[Entity], passages: list[PassageRecord]
    ) -> list[AliasEntry]:
        """Build alias mappings for entity variants.

        Args:
            entities: Entities to build aliases for
            passages: Source passages

        Returns:
            List of AliasEntry objects
        """
        ...

    def resolve(
        self, passages: list[PassageRecord]
    ) -> tuple[list[Entity], list[AliasEntry], list[EvidenceAnchor]]:
        """Full resolution pipeline.

        Args:
            passages: Passages to analyze

        Returns:
            Tuple of (entities, aliases, evidence_anchors)
        """
        ...


@runtime_checkable
class ObligationExtractorProtocol(Protocol):
    """Protocol for obligation extractors."""

    def extract(
        self, passages: list[PassageRecord], entities: list[Entity]
    ) -> tuple[list[Obligation], list[EvidenceAnchor]]:
        """Extract obligations from passages with evidence anchors.

        Args:
            passages: Passages to analyze
            entities: Known entities for context

        Returns:
            Tuple of (obligations, evidence_anchors)
        """
        ...


@runtime_checkable
class EventExtractorProtocol(Protocol):
    """Protocol for wiki event extractors."""

    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Event]:
        """Extract events referencing existing evidence anchors only."""
        ...


@runtime_checkable
class RelationshipExtractorProtocol(Protocol):
    """Protocol for wiki relationship extractors."""

    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Relationship]:
        """Extract relationships referencing existing evidence anchors only."""
        ...


@runtime_checkable
class DedupeMergerProtocol(Protocol):
    """Protocol for obligation deduplication."""

    @property
    def similarity_threshold(self) -> float:
        """Get similarity threshold for duplicate detection."""
        ...

    def compute_similarity(self, obl1: Obligation, obl2: Obligation) -> float:
        """Compute semantic similarity between two obligations.

        Args:
            obl1: First obligation
            obl2: Second obligation

        Returns:
            Similarity score between 0 and 1
        """
        ...

    def find_duplicates(self, obligations: list[Obligation]) -> list[tuple[str, str, float]]:
        """Find pairs of potentially duplicate obligations.

        Args:
            obligations: Obligations to analyze

        Returns:
            List of (obl_id_1, obl_id_2, similarity_score) tuples
        """
        ...

    def merge_obligations(self, obl1: Obligation, obl2: Obligation) -> Obligation:
        """Merge two obligations into one.

        Args:
            obl1: First obligation
            obl2: Second obligation

        Returns:
            Merged obligation
        """
        ...

    def merge(
        self, obligations: list[Obligation]
    ) -> tuple[list[Obligation], list[ObligationGraphEdge], float]:
        """Full merge pipeline.

        Args:
            obligations: Obligations to merge

        Returns:
            Tuple of (merged_obligations, duplicate_edges, dedupe_rate)
        """
        ...


@runtime_checkable
class QualityGatesProtocol(Protocol):
    """Protocol for quality gate validation."""

    def validate(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> tuple[bool, list[Finding]]:
        """Validate all artifacts and return pass/fail plus findings.

        Returns:
            Tuple of (passed, findings)
        """
        ...

    def validate_schema(self, artifact: Any, schema_path: Path) -> list[Finding]:
        """Validate artifact against JSON schema.

        Args:
            artifact: Artifact to validate
            schema_path: Path to JSON schema file

        Returns:
            List of Finding objects for any violations
        """
        ...

    def check_referential_integrity(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> list[Finding]:
        """Check referential integrity across all stores.

        Args:
            passages: All passages
            anchors: All evidence anchors
            entities: All entities
            aliases: All aliases
            obligations: All obligations

        Returns:
            List of Finding objects for any violations
        """
        ...

    def check_evidence_gate(self, obligations: list[Obligation]) -> list[Finding]:
        """Check that all obligations have evidence.

        Args:
            obligations: Obligations to check

        Returns:
            List of Finding objects for obligations without evidence
        """
        ...

    def detect_contradictions(self, obligations: list[Obligation]) -> list[Finding]:
        """Detect potential contradictions (WARN only in MVP).

        Args:
            obligations: Obligations to analyze

        Returns:
            List of Finding objects for contradictions (severity=WARN)
        """
        ...

    def run_all_gates(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> tuple[list[Finding], bool]:
        """Run all quality gates.

        Args:
            passages: All passages
            anchors: All evidence anchors
            entities: All entities
            aliases: All aliases
            obligations: All obligations

        Returns:
            Tuple of (all_findings, passed)
        """
        ...


@runtime_checkable
class DossierFormatterProtocol(Protocol):
    """Protocol for dossier output formatting."""

    def format_header(self, title: str) -> str:
        """Format the dossier header.

        Args:
            title: Dossier title

        Returns:
            Formatted header string
        """
        ...

    def format_category_section(self, category: Any, obligations: list[Obligation]) -> str:
        """Format a category section.

        Args:
            category: ObligationCategory
            obligations: Obligations in this category

        Returns:
            Formatted section string
        """
        ...

    def format_obligation(self, obl: Obligation, evidence: list[EvidenceAnchor]) -> str:
        """Format a single obligation.

        Args:
            obl: Obligation to format
            evidence: Evidence anchors for this obligation

        Returns:
            Formatted obligation string
        """
        ...

    def format_footer(self, metrics: dict[str, Any]) -> str:
        """Format the dossier footer.

        Args:
            metrics: Metrics to include

        Returns:
            Formatted footer string
        """
        ...


@runtime_checkable
class ExportRendererProtocol(Protocol):
    """Protocol for export rendering."""

    def render(self, obligations: list[Obligation]) -> str | Path:
        """Render dossier output, returning content or path."""
        ...

    def render_dossier(self, obligations: list[Obligation]) -> str:
        """Render the Unresolved Threads Dossier.

        Args:
            obligations: Obligations to include

        Returns:
            Rendered dossier content
        """
        ...

    def write_dossier(self, obligations: list[Obligation], output_path: Path) -> None:
        """Write dossier to file.

        Args:
            obligations: Obligations to include
            output_path: Path for output file
        """
        ...
