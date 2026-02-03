"""Reveal planner for v0.3 reveal ledger generation."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
from typing import TYPE_CHECKING

from showrunner.contracts import (
    CandidateTruth,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    RevealEntry,
)

if TYPE_CHECKING:
    from pathlib import Path


class RevealPlanner:
    """Generates reveal ledger entries from mystery obligations."""

    def plan(
        self, obligations: list[Obligation], anchors: list[EvidenceAnchor]
    ) -> list[RevealEntry]:
        if not obligations:
            return []

        anchor_map = {anchor.anchor_id: anchor for anchor in anchors}
        mysteries = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        entries: list[RevealEntry] = []

        for obligation in sorted(mysteries, key=lambda o: o.obligation_id):
            evidence_for = [
                anchor_id for anchor_id in obligation.evidence_anchor_ids if anchor_id in anchor_map
            ]
            truth = CandidateTruth(
                truth_id=self._truth_id(obligation),
                description="Candidate truth derived from evidence anchors",
                evidence_for=list(evidence_for),
                evidence_against=[],
                likelihood=0.5,
            )
            entries.append(
                RevealEntry(
                    reveal_id=self._reveal_id(obligation),
                    mystery_obligation_id=obligation.obligation_id,
                    mystery_description=obligation.description,
                    candidate_truths=[truth],
                    selected_truth=None,
                    reveal_placement=None,
                    characters_who_learn=list(obligation.related_entity_ids),
                    dramatic_impact="moderate",
                )
            )

        return entries

    def render_csv(self, entries: list[RevealEntry]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "reveal_id",
                "mystery_obligation_id",
                "mystery_description",
                "candidate_truth_ids",
                "selected_truth",
                "reveal_placement",
                "characters_who_learn",
                "dramatic_impact",
            ]
        )
        for entry in entries:
            writer.writerow(
                [
                    entry.reveal_id,
                    entry.mystery_obligation_id,
                    entry.mystery_description,
                    ";".join([t.truth_id for t in entry.candidate_truths]),
                    entry.selected_truth or "",
                    entry.reveal_placement or "",
                    ";".join(entry.characters_who_learn),
                    entry.dramatic_impact,
                ]
            )
        return output.getvalue()

    def export_csv(self, entries: list[RevealEntry], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_csv(entries), encoding="utf-8")

    def _reveal_id(self, obligation: Obligation) -> str:
        content = f"reveal:{obligation.obligation_id}"
        return f"reveal_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _truth_id(self, obligation: Obligation) -> str:
        content = f"truth:{obligation.obligation_id}"
        return f"truth_{hashlib.sha256(content.encode()).hexdigest()[:12]}"
