"""ExportRenderer module for generating dossiers from validated stores.

This module provides:
- DossierFormatter: Protocol for swappable output formatters (Strategy Pattern)
- MarkdownFormatter: Markdown implementation of DossierFormatter
- ExportRenderer: Renders dossiers from validated canon stores

OOP Principles Applied:
- Single Responsibility: Formatting logic separated from data access/rendering logic
- Dependency Injection: Stores and formatter passed via constructor
- Strategy Pattern: Formatter is swappable at runtime
- No Primitive Obsession: Uses domain objects throughout
"""

from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Protocol

from showrunner.contracts import (
    Entity,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    PassageRecord,
)


class DossierFormatter(Protocol):
    """Strategy protocol for formatting dossier output.

    Implementations of this protocol define how dossier content is formatted
    for a specific output format (e.g., Markdown, HTML, plain text).

    This enables the Strategy Pattern: different formatters can be injected
    into ExportRenderer to produce different output formats.
    """

    @abstractmethod
    def format_header(self, title: str) -> str:
        """Format the dossier header.

        Args:
            title: The dossier title.

        Returns:
            Formatted header string.
        """
        ...

    @abstractmethod
    def format_category_section(
        self, category: ObligationCategory, obligations: list[Obligation]
    ) -> str:
        """Format a category section with its obligations.

        Args:
            category: The obligation category.
            obligations: List of obligations in this category.

        Returns:
            Formatted category section string.
        """
        ...

    @abstractmethod
    def format_obligation(
        self, obl: Obligation, evidence: list[EvidenceAnchor]
    ) -> str:
        """Format a single obligation with its evidence.

        Args:
            obl: The obligation to format.
            evidence: Evidence anchors supporting this obligation.

        Returns:
            Formatted obligation string.
        """
        ...

    @abstractmethod
    def format_footer(self, metrics: dict) -> str:
        """Format the dossier footer.

        Args:
            metrics: Dictionary of dossier metrics (counts, etc.).

        Returns:
            Formatted footer string.
        """
        ...


class MarkdownFormatter:
    """Markdown implementation of DossierFormatter.

    Produces GitHub-flavored Markdown output for the dossier.
    """

    # Category display name mapping
    _CATEGORY_DISPLAY_NAMES: dict[ObligationCategory, str] = {
        ObligationCategory.PROPHECY_VISION: "Prophecies & Visions",
        ObligationCategory.MYSTERY: "Mysteries",
        ObligationCategory.CHEKHOV_GUN: "Chekhov's Guns",
        ObligationCategory.PLOT_THREAD: "Plot Threads",
    }

    def format_header(self, title: str) -> str:
        """Format the dossier header with title and timestamp.

        Args:
            title: The dossier title.

        Returns:
            Markdown-formatted header with H1 title and generation timestamp.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"# {title}\nGenerated: {timestamp}\n"

    def format_category_section(
        self, category: ObligationCategory, obligations: list[Obligation]
    ) -> str:
        """Format a category section with H2 heading and count.

        Args:
            category: The obligation category.
            obligations: List of obligations in this category.

        Returns:
            Markdown-formatted category section header.
        """
        display_name = self._CATEGORY_DISPLAY_NAMES.get(category, category.value)
        count = len(obligations)
        return f"\n## {display_name} ({count})\n"

    def format_obligation(
        self, obl: Obligation, evidence: list[EvidenceAnchor]
    ) -> str:
        """Format an obligation with confidence, last seen, and evidence.

        Args:
            obl: The obligation to format.
            evidence: Evidence anchors supporting this obligation.

        Returns:
            Markdown-formatted obligation with H3 heading and details.
        """
        lines = [
            f"### {obl.description}",
            f"- **Confidence:** {obl.confidence:.2f}",
            f"- **Last Seen:** {obl.last_seen_passage_id}",
            "- **Evidence:**",
        ]

        if evidence:
            for anchor in evidence:
                lines.append(f'  > "{anchor.excerpt}" -- {anchor.passage_id}')
        else:
            lines.append("  > (No evidence available)")

        return "\n".join(lines) + "\n"

    def format_footer(self, metrics: dict) -> str:
        """Format the dossier footer with separator and validation notice.

        Args:
            metrics: Dictionary of dossier metrics.

        Returns:
            Markdown-formatted footer with horizontal rule and notice.
        """
        return "\n---\n*Generated from validated canon stores*\n"


class ExportRenderer:
    """Renders dossiers from validated canon stores.

    This class follows several OOP principles:
    - Single Responsibility: Only handles dossier rendering, not data loading
    - Dependency Injection: Formatter and stores injected via constructor
    - Strategy Pattern: Formatter can be swapped for different output formats
    - No Primitive Obsession: Works with domain objects, not raw dicts

    The renderer generates output ONLY from validated stores, ensuring
    no direct LLM-to-markdown generation occurs.
    """

    # Category ordering for dossier sections
    _CATEGORY_ORDER: list[ObligationCategory] = [
        ObligationCategory.PROPHECY_VISION,
        ObligationCategory.MYSTERY,
        ObligationCategory.CHEKHOV_GUN,
        ObligationCategory.PLOT_THREAD,
    ]

    def __init__(
        self,
        formatter: DossierFormatter,
        passages: list[PassageRecord],
        entities: list[Entity],
        anchors: list[EvidenceAnchor],
    ) -> None:
        """Initialize the ExportRenderer with injected dependencies.

        Args:
            formatter: The formatter strategy to use for output generation.
            passages: List of passage records from validated stores.
            entities: List of entities from validated stores.
            anchors: List of evidence anchors from validated stores.
        """
        self._formatter = formatter
        self._passages: dict[str, PassageRecord] = {
            p.passage_id: p for p in passages
        }
        self._entities: dict[str, Entity] = {e.entity_id: e for e in entities}
        self._anchors: dict[str, EvidenceAnchor] = {
            a.anchor_id: a for a in anchors
        }

    def _group_by_category(
        self, obligations: list[Obligation]
    ) -> dict[ObligationCategory, list[Obligation]]:
        """Group obligations by their category.

        Args:
            obligations: List of obligations to group.

        Returns:
            Dictionary mapping categories to lists of obligations.
        """
        grouped: dict[ObligationCategory, list[Obligation]] = defaultdict(list)
        for obl in obligations:
            grouped[obl.category].append(obl)
        return dict(grouped)

    def _resolve_evidence(self, obl: Obligation) -> list[EvidenceAnchor]:
        """Resolve evidence anchor IDs to evidence anchor objects.

        Handles missing anchors gracefully by returning only found anchors.

        Args:
            obl: The obligation whose evidence to resolve.

        Returns:
            List of resolved EvidenceAnchor objects.
        """
        evidence = []
        for anchor_id in obl.evidence_anchor_ids:
            if anchor_id in self._anchors:
                evidence.append(self._anchors[anchor_id])
        return evidence

    def render_dossier(self, obligations: list[Obligation]) -> str:
        """Render the Unresolved Threads Dossier from obligations.

        Generates a complete dossier with:
        - Header with title and timestamp
        - Category sections in defined order (Prophecies, Mysteries, Chekhov, Plot)
        - Individual obligations with confidence, last seen, and evidence
        - Footer with validation notice

        Args:
            obligations: List of obligations to include in the dossier.

        Returns:
            Complete rendered dossier as a string.
        """
        sections = []

        # Add header
        sections.append(self._formatter.format_header("Unresolved Threads Dossier"))

        # Group obligations by category
        grouped = self._group_by_category(obligations)

        # Add category sections in specified order
        for category in self._CATEGORY_ORDER:
            if category in grouped and grouped[category]:
                category_obligations = grouped[category]
                sections.append(
                    self._formatter.format_category_section(category, category_obligations)
                )

                # Add each obligation in the category
                for obl in category_obligations:
                    evidence = self._resolve_evidence(obl)
                    sections.append(self._formatter.format_obligation(obl, evidence))

        # Add footer
        metrics = {
            "total_obligations": len(obligations),
            "categories": len(grouped),
        }
        sections.append(self._formatter.format_footer(metrics))

        return "".join(sections)

    def write_dossier(
        self, obligations: list[Obligation], output_path: Path
    ) -> None:
        """Write dossier to file.

        Creates parent directories if they don't exist.
        Uses UTF-8 encoding for the output file.

        Args:
            obligations: List of obligations to include in the dossier.
            output_path: Path where the dossier file should be written.
        """
        content = self.render_dossier(obligations)

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with UTF-8 encoding
        output_path.write_text(content, encoding="utf-8")
