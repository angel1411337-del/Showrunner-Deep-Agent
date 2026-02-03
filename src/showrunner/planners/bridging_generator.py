"""Generate bridging beats between convergence points."""

from __future__ import annotations

from showrunner.contracts import Beat, OutlineSection


class BridgingGenerator:
    """Generates bridging beats to connect convergence points."""

    def generate(self, outline: list[OutlineSection]) -> list[Beat]:
        """Generate bridging beats based on convergence points in the outline."""
        bridging_beats: list[Beat] = []
        for section in outline:
            for index, convergence in enumerate(section.convergence_points, start=1):
                bridging_beats.append(
                    Beat(
                        beat_id=f"bridge_{section.section_id}_{index:02d}",
                        description=f"Bridge convergence: {convergence.description}",
                        chapter_hint=convergence.suggested_placement,
                        pov_character=None,
                        obligations_addressed=convergence.converging_obligations,
                        entities_involved=[],
                        is_bridging=True,
                    )
                )
        return bridging_beats
