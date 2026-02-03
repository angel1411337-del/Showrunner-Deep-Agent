"""Outline planner for v0.2 master outline generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from showrunner.contracts import (
    Beat,
    ConvergencePoint,
    Entity,
    Obligation,
    OutlineSection,
)
from showrunner.planners.bridging_generator import BridgingGenerator
from showrunner.planners.convergence_detector import ConvergenceDetector


class OutlinePlanner:
    """Generates master outline sections from obligations and entities."""

    def __init__(
        self,
        convergence_detector: ConvergenceDetector | None = None,
        bridging_generator: BridgingGenerator | None = None,
    ) -> None:
        self._convergence_detector = convergence_detector or ConvergenceDetector()
        self._bridging_generator = bridging_generator or BridgingGenerator()

    def plan(self, obligations: list[Obligation], entities: list[Entity]) -> list[OutlineSection]:
        """Generate outline sections for books 6 and 7."""
        if not obligations:
            return []

        entity_map = {entity.entity_id: entity for entity in entities}
        sorted_obligations = sorted(obligations, key=lambda o: o.obligation_id)
        midpoint = max(1, len(sorted_obligations) // 2)
        book6_obls = sorted_obligations[:midpoint]
        book7_obls = sorted_obligations[midpoint:]

        sections: list[OutlineSection] = [
            OutlineSection(
                section_id="book_6",
                title="Book 6 Outline",
                book_number=6,
                beats=self._build_beats(book6_obls, entity_map, 6),
                convergence_points=[],
            ),
            OutlineSection(
                section_id="book_7",
                title="Book 7 Outline",
                book_number=7,
                beats=self._build_beats(book7_obls, entity_map, 7),
                convergence_points=[],
            ),
        ]

        convergence_points = self._convergence_detector.detect(sections)
        sections = self._assign_convergences(sections, convergence_points)

        bridging_beats = self._bridging_generator.generate(sections)
        sections = self._append_bridging(sections, bridging_beats)

        return sections

    def export_outline(
        self,
        outline: list[OutlineSection],
        obligations: list[Obligation],
        output_path: Path,
    ) -> None:
        """Render outline and write to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.render_markdown(outline, obligations)
        output_path.write_text(content, encoding="utf-8")

    def render_markdown(self, outline: list[OutlineSection], obligations: list[Obligation]) -> str:
        """Render outline to Markdown with coverage mapping."""
        lines: list[str] = ["# Master Outline (Books 6-7)", ""]

        for section in outline:
            lines.append(f"## {section.title}")
            lines.append("")
            for beat in section.beats:
                lines.append(f"### {beat.beat_id}")
                lines.append(beat.description)
                if beat.chapter_hint:
                    lines.append(f"- Chapter hint: {beat.chapter_hint}")
                if beat.pov_character:
                    lines.append(f"- POV: {beat.pov_character}")
                if beat.is_bridging:
                    lines.append("- Bridging beat: yes")
                if beat.obligations_addressed:
                    lines.append(f"- Obligations: {', '.join(sorted(beat.obligations_addressed))}")
                if beat.entities_involved:
                    lines.append(f"- Entities: {', '.join(sorted(beat.entities_involved))}")
                lines.append("")

            if section.convergence_points:
                lines.append("### Convergence Points")
                for convergence in section.convergence_points:
                    lines.append(f"- {convergence.description}")
                    lines.append(
                        f"  - Obligations: {', '.join(convergence.converging_obligations)}"
                    )
                    lines.append(f"  - Placement: {convergence.suggested_placement}")
                    lines.append(f"  - Dramatic weight: {convergence.dramatic_weight:.2f}")
                lines.append("")

        lines.append("## Coverage Mapping")
        coverage = self._build_coverage_map(outline, obligations)
        for obligation_id, beat_ids in coverage.items():
            status = "fully_addressed" if beat_ids else "unaddressed"
            beat_list = ", ".join(beat_ids) if beat_ids else "—"
            lines.append(f"- {obligation_id}: {status} (beats: {beat_list})")

        return "\n".join(lines).rstrip() + "\n"

    def _build_beats(
        self,
        obligations: list[Obligation],
        entity_map: dict[str, Entity],
        book_number: int,
    ) -> list[Beat]:
        beats: list[Beat] = []
        for index, obligation in enumerate(obligations, start=1):
            pov_character = None
            if obligation.related_entity_ids:
                first_entity = entity_map.get(obligation.related_entity_ids[0])
                pov_character = first_entity.canonical_name if first_entity else None
            beats.append(
                Beat(
                    beat_id=f"book{book_number}_beat_{index:03d}",
                    description=obligation.description,
                    chapter_hint=None,
                    pov_character=pov_character,
                    obligations_addressed=[obligation.obligation_id],
                    entities_involved=list(obligation.related_entity_ids),
                    is_bridging=False,
                )
            )
        return beats

    def _assign_convergences(
        self,
        outline: list[OutlineSection],
        convergence_points: list[ConvergencePoint],
    ) -> list[OutlineSection]:
        if not convergence_points:
            return outline

        assigned: dict[str, list[ConvergencePoint]] = {s.section_id: [] for s in outline}
        for point in convergence_points:
            target_section = outline[0]
            if "Book 7" in point.suggested_placement:
                target_section = outline[-1]
            assigned[target_section.section_id].append(point)

        updated_sections: list[OutlineSection] = []
        for section in outline:
            updated_sections.append(
                OutlineSection(
                    section_id=section.section_id,
                    title=section.title,
                    book_number=section.book_number,
                    beats=list(section.beats),
                    convergence_points=assigned.get(section.section_id, []),
                )
            )
        return updated_sections

    def _append_bridging(
        self, outline: list[OutlineSection], bridging_beats: list[Beat]
    ) -> list[OutlineSection]:
        if not bridging_beats:
            return outline

        beats_by_section: dict[str, list[Beat]] = {s.section_id: list(s.beats) for s in outline}
        for beat in bridging_beats:
            for section in outline:
                if beat.beat_id.startswith(f"bridge_{section.section_id}"):
                    beats_by_section[section.section_id].append(beat)

        updated_sections: list[OutlineSection] = []
        for section in outline:
            updated_sections.append(
                OutlineSection(
                    section_id=section.section_id,
                    title=section.title,
                    book_number=section.book_number,
                    beats=beats_by_section.get(section.section_id, []),
                    convergence_points=list(section.convergence_points),
                )
            )
        return updated_sections

    def _build_coverage_map(
        self, outline: list[OutlineSection], obligations: list[Obligation]
    ) -> dict[str, list[str]]:
        coverage: dict[str, list[str]] = {obl.obligation_id: [] for obl in obligations}
        for section in outline:
            for beat in section.beats:
                for obligation_id in beat.obligations_addressed:
                    if obligation_id in coverage:
                        coverage[obligation_id].append(beat.beat_id)
        return coverage
