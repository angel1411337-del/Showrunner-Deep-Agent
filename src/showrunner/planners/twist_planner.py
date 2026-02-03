"""Twist planner for v0.4 twist bank generation."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from showrunner.contracts import EvidenceAnchor, Obligation, TwistProposal

if TYPE_CHECKING:
    from pathlib import Path


class TwistPlanner:
    """Generates twist proposals from obligations."""

    def plan(
        self, obligations: list[Obligation], anchors: list[EvidenceAnchor]
    ) -> list[TwistProposal]:
        if not obligations:
            return []

        anchor_map = {anchor.anchor_id: anchor for anchor in anchors}
        twists: list[TwistProposal] = []

        for obligation in sorted(obligations, key=lambda o: o.obligation_id):
            evidence_support = [
                anchor_id for anchor_id in obligation.evidence_anchor_ids if anchor_id in anchor_map
            ]
            twists.append(
                TwistProposal(
                    twist_id=self._twist_id(obligation),
                    description=f"Twist proposal derived from obligation {obligation.obligation_id}",
                    twist_type="revelation",
                    affected_obligations=[obligation.obligation_id],
                    affected_entities=list(obligation.related_entity_ids),
                    evidence_support=evidence_support,
                    contradictions=[],
                    required_setup=[],
                    backfill_suggestions=[],
                    reader_predictability=0.5,
                    thematic_alignment=0.5,
                    risk_notes=[],
                )
            )

        return twists

    def render_markdown(self, twists: list[TwistProposal]) -> str:
        lines: list[str] = ["# Twist Bank", ""]
        for twist in twists:
            lines.append(f"## {twist.twist_id}")
            lines.append(twist.description)
            lines.append(f"- Type: {twist.twist_type}")
            if twist.affected_obligations:
                lines.append(f"- Obligations: {', '.join(twist.affected_obligations)}")
            if twist.affected_entities:
                lines.append(f"- Entities: {', '.join(twist.affected_entities)}")
            if twist.evidence_support:
                lines.append(f"- Evidence: {', '.join(twist.evidence_support)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def export_markdown(self, twists: list[TwistProposal], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_markdown(twists), encoding="utf-8")

    def _twist_id(self, obligation: Obligation) -> str:
        content = f"twist:{obligation.obligation_id}"
        return f"twist_{hashlib.sha256(content.encode()).hexdigest()[:12]}"
