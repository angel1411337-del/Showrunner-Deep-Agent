"""Detect convergence points in an outline."""

from __future__ import annotations

from collections import defaultdict

from showrunner.contracts import ConvergencePoint, OutlineSection


class ConvergenceDetector:
    """Detects where multiple plot threads converge."""

    def detect(self, outline: list[OutlineSection]) -> list[ConvergencePoint]:
        """Detect convergence points from outline sections."""
        if not outline:
            return []

        entity_to_obligations: dict[str, set[str]] = defaultdict(set)
        entity_to_books: dict[str, set[int]] = defaultdict(set)

        for section in outline:
            for beat in section.beats:
                for entity_id in beat.entities_involved:
                    entity_to_books[entity_id].add(section.book_number)
                    for obligation_id in beat.obligations_addressed:
                        entity_to_obligations[entity_id].add(obligation_id)

        convergence_points: list[ConvergencePoint] = []
        for entity_id, obligations in sorted(entity_to_obligations.items()):
            if len(obligations) < 2:
                continue

            books = sorted(entity_to_books.get(entity_id, set()))
            if len(books) >= 2:
                placement = "Between books 6 and 7"
            elif books:
                placement = f"Book {books[0]} midpoint"
            else:
                placement = "Outline midpoint"

            weight = min(1.0, 0.3 + 0.1 * len(obligations))
            convergence_points.append(
                ConvergencePoint(
                    convergence_id=f"conv_{entity_id}",
                    description=f"Threads converge around entity {entity_id}",
                    converging_obligations=sorted(obligations),
                    suggested_placement=placement,
                    dramatic_weight=weight,
                )
            )

        return convergence_points
