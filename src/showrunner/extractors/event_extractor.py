"""Rule-based event extractor for wiki events.

MVP implementation: detect simple event keywords and emit Event records
with provenance (existing evidence anchors only) and dual time axes.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from showrunner.contracts import Entity, EntityType, EvidenceAnchor, Obligation, PassageRecord
from showrunner.contracts.wiki import Event, EventType, StoryOrder, StoryTime


class EventExtractor:
    """Extracts canonical events from passages using simple keyword rules."""

    _BATTLE_PATTERNS = [
        re.compile(r"\bbattle\b", re.IGNORECASE),
        re.compile(r"\bwar\b", re.IGNORECASE),
        re.compile(r"\bsiege\b", re.IGNORECASE),
    ]
    _DEATH_PATTERNS = [
        re.compile(r"\bdied\b", re.IGNORECASE),
        re.compile(r"\bkilled\b", re.IGNORECASE),
        re.compile(r"\bslain\b", re.IGNORECASE),
    ]
    _TREATY_PATTERNS = [
        re.compile(r"\btreaty\b", re.IGNORECASE),
        re.compile(r"\btruce\b", re.IGNORECASE),
    ]
    _BETRAYAL_PATTERNS = [
        re.compile(r"\bbetray\w*\b", re.IGNORECASE),
        re.compile(r"\btreachery\b", re.IGNORECASE),
    ]
    _MARRIAGE_PATTERNS = [
        re.compile(r"\bmarriage\b", re.IGNORECASE),
        re.compile(r"\bmarried\b", re.IGNORECASE),
        re.compile(r"\bwedding\b", re.IGNORECASE),
    ]
    _CORONATION_PATTERNS = [
        re.compile(r"\bcoronation\b", re.IGNORECASE),
        re.compile(r"\bcrowned\b", re.IGNORECASE),
    ]
    _TRAVEL_PATTERNS = [
        re.compile(r"\bjourney\b", re.IGNORECASE),
        re.compile(r"\btraveled\b", re.IGNORECASE),
        re.compile(r"\bset out\b", re.IGNORECASE),
        re.compile(r"\bdeparted\b", re.IGNORECASE),
    ]
    _DISCOVERY_PATTERNS = [
        re.compile(r"\bdiscovered\b", re.IGNORECASE),
        re.compile(r"\bfound\b", re.IGNORECASE),
        re.compile(r"\buncovered\b", re.IGNORECASE),
    ]

    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Event]:
        anchor_map = self._anchors_by_passage(anchors)
        events: list[Event] = []

        for passage in passages:
            event_type = self._classify_event(passage.text)
            if event_type is None:
                continue

            anchor_ids = self._anchor_ids_for_passage(passage.passage_id, anchor_map)
            if not anchor_ids:
                # Provenance required: skip if no anchors for this passage.
                continue

            participants = self._find_participants(passage.text, entities)
            location_id = self._find_location(passage.text, entities)
            related_obligations = self._related_obligations(anchor_ids, obligations)

            title = self._build_title(event_type, location_id, entities)
            description = passage.text.strip()

            story_order = StoryOrder(
                order_index=passage.paragraph_index,
                order_label=passage.passage_id,
                source_id=passage.source_id,
                passage_id=passage.passage_id,
            )
            story_time = StoryTime(time_label="unknown")

            event_id = self._generate_event_id(
                event_type=event_type,
                passage_id=passage.passage_id,
                anchor_id=anchor_ids[0],
                title=title,
            )

            events.append(
                Event(
                    event_id=event_id,
                    event_type=event_type,
                    title=title,
                    description=description,
                    participant_entity_ids=participants,
                    location_entity_id=location_id,
                    related_obligation_ids=related_obligations,
                    evidence_anchor_ids=anchor_ids,
                    story_time=story_time,
                    story_order=story_order,
                    created_at=datetime.now(),
                )
            )

        return events

    def _classify_event(self, text: str) -> EventType | None:
        if self._matches_any(text, self._BATTLE_PATTERNS):
            return EventType.BATTLE
        if self._matches_any(text, self._DEATH_PATTERNS):
            return EventType.DEATH
        if self._matches_any(text, self._TREATY_PATTERNS):
            return EventType.TREATY
        if self._matches_any(text, self._BETRAYAL_PATTERNS):
            return EventType.BETRAYAL
        if self._matches_any(text, self._MARRIAGE_PATTERNS):
            return EventType.MARRIAGE
        if self._matches_any(text, self._CORONATION_PATTERNS):
            return EventType.CORONATION
        if self._matches_any(text, self._TRAVEL_PATTERNS):
            return EventType.TRAVEL
        if self._matches_any(text, self._DISCOVERY_PATTERNS):
            return EventType.DISCOVERY
        return None

    def _matches_any(self, text: str, patterns: list[re.Pattern[str]]) -> bool:
        return any(pattern.search(text) for pattern in patterns)

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

    def _find_participants(self, text: str, entities: list[Entity]) -> list[str]:
        lowered = text.lower()
        participants: list[tuple[int, str]] = []
        for entity in entities:
            name = entity.canonical_name.lower()
            idx = lowered.find(name)
            if idx != -1:
                participants.append((idx, entity.entity_id))
        participants.sort(key=lambda item: item[0])
        return [entity_id for _idx, entity_id in participants]

    def _find_location(self, text: str, entities: list[Entity]) -> str | None:
        lowered = text.lower()
        for entity in entities:
            if entity.entity_type != EntityType.PLACE:
                continue
            if entity.canonical_name.lower() in lowered:
                return entity.entity_id
        return None

    def _related_obligations(
        self, anchor_ids: list[str], obligations: list[Obligation]
    ) -> list[str]:
        related: list[str] = []
        anchor_set = set(anchor_ids)
        for obligation in obligations:
            if anchor_set.intersection(obligation.evidence_anchor_ids):
                related.append(obligation.obligation_id)
        return related

    def _build_title(
        self, event_type: EventType, location_id: str | None, entities: list[Entity]
    ) -> str:
        label = event_type.value.replace("_", " ").title()
        if not location_id:
            return label
        location_name = self._entity_name(location_id, entities)
        if event_type == EventType.BATTLE:
            return f"Battle of {location_name}"
        return f"{label} at {location_name}"

    def _entity_name(self, entity_id: str, entities: list[Entity]) -> str:
        for entity in entities:
            if entity.entity_id == entity_id:
                return entity.canonical_name
        return entity_id

    def _generate_event_id(
        self, event_type: EventType, passage_id: str, anchor_id: str, title: str
    ) -> str:
        content = f"{event_type.value}|{passage_id}|{anchor_id}|{title}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        return f"evt_{digest}"
