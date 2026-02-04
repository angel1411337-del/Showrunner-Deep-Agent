"""Rule-based relationship extractor for wiki relationships."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import TYPE_CHECKING

from showrunner.contracts.wiki import Relationship, RelationshipType, StoryOrder, StoryTime

if TYPE_CHECKING:
    from showrunner.contracts import Entity, EvidenceAnchor, Obligation, PassageRecord


class RelationshipExtractor:
    """Extracts relationships between entities using simple keyword rules."""

    _RELATION_PATTERNS: list[tuple[RelationshipType, re.Pattern[str]]] = [
        (RelationshipType.ALLIANCE, re.compile(r"\ballied with\b", re.IGNORECASE)),
        (RelationshipType.ENMITY, re.compile(r"\benemy\b|\benmity\b", re.IGNORECASE)),
        (
            RelationshipType.KINSHIP,
            re.compile(r"\bson of\b|\bdaughter of\b|\bbrother\b|\bsister\b", re.IGNORECASE),
        ),
        (RelationshipType.OATH, re.compile(r"\bswore\b|\boath\b", re.IGNORECASE)),
        (RelationshipType.DEBT, re.compile(r"\bowed\b|\bdebt\b", re.IGNORECASE)),
        (RelationshipType.COMMAND, re.compile(r"\bcommanded\b|\bordered\b", re.IGNORECASE)),
        (RelationshipType.MEMBERSHIP, re.compile(r"\bmember of\b|\bjoined\b", re.IGNORECASE)),
        (RelationshipType.OWNERSHIP, re.compile(r"\bowned\b|\bbelongs to\b", re.IGNORECASE)),
    ]

    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Relationship]:
        anchor_map = self._anchors_by_passage(anchors)
        relationships: list[Relationship] = []

        for passage in passages:
            relation_type = self._classify_relationship(passage.text)
            if relation_type is None:
                continue

            anchor_ids = self._anchor_ids_for_passage(passage.passage_id, anchor_map)
            if not anchor_ids:
                continue

            entity_ids = self._ordered_entity_mentions(passage.text, entities)
            if len(entity_ids) < 2:
                continue

            source_id, target_id = entity_ids[0], entity_ids[1]
            description = self._build_description(relation_type, source_id, target_id, entities)

            story_order = StoryOrder(
                order_index=passage.paragraph_index,
                order_label=passage.passage_id,
                source_id=passage.source_id,
                passage_id=passage.passage_id,
            )
            story_time = StoryTime(time_label="unknown")

            relationship_id = self._generate_relationship_id(
                relation_type=relation_type,
                passage_id=passage.passage_id,
                anchor_id=anchor_ids[0],
                source_id=source_id,
                target_id=target_id,
            )

            relationships.append(
                Relationship(
                    relationship_id=relationship_id,
                    relation_type=relation_type,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    description=description,
                    evidence_anchor_ids=anchor_ids,
                    story_time=story_time,
                    story_order=story_order,
                    created_at=datetime.now(),
                )
            )

        return relationships

    def _classify_relationship(self, text: str) -> RelationshipType | None:
        for relation_type, pattern in self._RELATION_PATTERNS:
            if pattern.search(text):
                return relation_type
        return None

    def _anchors_by_passage(self, anchors: list[EvidenceAnchor]) -> dict[str, list[EvidenceAnchor]]:
        anchor_map: dict[str, list[EvidenceAnchor]] = {}
        for anchor in anchors:
            anchor_map.setdefault(anchor.passage_id, []).append(anchor)
        return anchor_map

    def _anchor_ids_for_passage(
        self, passage_id: str, anchor_map: dict[str, list[EvidenceAnchor]]
    ) -> list[str]:
        anchors = anchor_map.get(passage_id, [])
        return [anchor.anchor_id for anchor in sorted(anchors, key=lambda a: a.anchor_id)]

    def _ordered_entity_mentions(self, text: str, entities: list[Entity]) -> list[str]:
        lowered = text.lower()
        mentions: list[tuple[int, str]] = []
        for entity in entities:
            name = entity.canonical_name.lower()
            idx = lowered.find(name)
            if idx != -1:
                mentions.append((idx, entity.entity_id))
        mentions.sort(key=lambda item: item[0])
        return [entity_id for _idx, entity_id in mentions]

    def _build_description(
        self,
        relation_type: RelationshipType,
        source_id: str,
        target_id: str,
        entities: list[Entity],
    ) -> str:
        source_name = self._entity_name(source_id, entities)
        target_name = self._entity_name(target_id, entities)
        if relation_type == RelationshipType.ALLIANCE:
            return f"Alliance between {source_name} and {target_name}."
        if relation_type == RelationshipType.ENMITY:
            return f"Enmity between {source_name} and {target_name}."
        return f"{relation_type.value.title()} between {source_name} and {target_name}."

    def _entity_name(self, entity_id: str, entities: list[Entity]) -> str:
        for entity in entities:
            if entity.entity_id == entity_id:
                return entity.canonical_name
        return entity_id

    def _generate_relationship_id(
        self,
        relation_type: RelationshipType,
        passage_id: str,
        anchor_id: str,
        source_id: str,
        target_id: str,
    ) -> str:
        content = f"{relation_type.value}|{passage_id}|{anchor_id}|{source_id}|{target_id}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        return f"rel_{digest}"
