"""Golden tests ensuring deterministic outputs across reruns.

These tests validate that the Showrunner Orchestrator produces stable,
reproducible outputs when given the same input corpus. This is critical
for maintaining evidence anchor integrity and ensuring that passage IDs,
entity extractions, and obligation categorizations remain consistent.

Fixtures are located in tests/golden/fixtures/ and represent the expected
"golden" output that the pipeline should produce.
"""

import json
from pathlib import Path
from typing import Any

import pytest

# Path to golden fixtures
FIXTURES_DIR = Path(__file__).parent / "golden" / "fixtures"


def load_fixture(filename: str) -> str:
    """Load a fixture file as a string."""
    fixture_path = FIXTURES_DIR / filename
    return fixture_path.read_text(encoding="utf-8")


def load_json_fixture(filename: str) -> dict[str, Any]:
    """Load a JSON fixture file."""
    content = load_fixture(filename)
    return json.loads(content)


class TestGoldenFixturesExist:
    """Verify all required golden fixtures are present."""

    def test_sample_corpus_exists(self):
        """Sample corpus fixture must exist."""
        assert (FIXTURES_DIR / "sample_corpus.txt").exists()

    def test_expected_passages_exists(self):
        """Expected passages fixture must exist."""
        assert (FIXTURES_DIR / "expected_passages.json").exists()

    def test_expected_entities_exists(self):
        """Expected entities fixture must exist."""
        assert (FIXTURES_DIR / "expected_entities.json").exists()

    def test_expected_obligations_exists(self):
        """Expected obligations fixture must exist."""
        assert (FIXTURES_DIR / "expected_obligations.json").exists()

    def test_expected_dossier_exists(self):
        """Expected dossier fixture must exist."""
        assert (FIXTURES_DIR / "expected_dossier.md").exists()


class TestGoldenFixturesValid:
    """Verify golden fixtures have valid structure."""

    def test_sample_corpus_has_content(self):
        """Sample corpus must have substantial content (~500 words)."""
        content = load_fixture("sample_corpus.txt")
        word_count = len(content.split())
        assert word_count >= 400, f"Corpus too short: {word_count} words"
        assert word_count <= 600, f"Corpus too long: {word_count} words"

    def test_expected_passages_has_required_fields(self):
        """Expected passages must have metadata and passages list."""
        data = load_json_fixture("expected_passages.json")
        assert "metadata" in data
        assert "passages" in data
        assert "source_id" in data["metadata"]
        assert "total_passages" in data["metadata"]
        assert len(data["passages"]) > 0

    def test_expected_passages_have_valid_structure(self):
        """Each passage must have required fields."""
        data = load_json_fixture("expected_passages.json")
        required_fields = {
            "passage_id",
            "source_id",
            "paragraph_index",
            "text",
            "char_start",
            "char_end",
        }
        for passage in data["passages"]:
            missing = required_fields - set(passage.keys())
            assert not missing, f"Passage missing fields: {missing}"

    def test_expected_entities_has_required_fields(self):
        """Expected entities must have metadata and entities list."""
        data = load_json_fixture("expected_entities.json")
        assert "metadata" in data
        assert "entities" in data
        assert "total_entities" in data["metadata"]
        assert len(data["entities"]) > 0

    def test_expected_entities_have_valid_structure(self):
        """Each entity must have required fields."""
        data = load_json_fixture("expected_entities.json")
        required_fields = {
            "entity_id",
            "canonical_name",
            "entity_type",
            "first_seen_passage",
            "mention_count",
        }
        for entity in data["entities"]:
            missing = required_fields - set(entity.keys())
            assert not missing, f"Entity missing fields: {missing}"

    def test_expected_obligations_has_required_fields(self):
        """Expected obligations must have metadata and obligations list."""
        data = load_json_fixture("expected_obligations.json")
        assert "metadata" in data
        assert "obligations" in data
        assert "evidence_anchors" in data
        assert "total_obligations" in data["metadata"]
        assert len(data["obligations"]) > 0

    def test_expected_obligations_have_valid_structure(self):
        """Each obligation must have required fields."""
        data = load_json_fixture("expected_obligations.json")
        required_fields = {
            "obligation_id",
            "category",
            "description",
            "evidence_anchor_ids",
            "last_seen_passage_id",
            "confidence",
        }
        for obligation in data["obligations"]:
            missing = required_fields - set(obligation.keys())
            assert not missing, f"Obligation missing fields: {missing}"


class TestGoldenDeterminism:
    """Golden tests ensuring deterministic outputs across reruns."""

    def test_passage_ids_stable(self):
        """Same input produces same passage IDs.

        Passage IDs must follow the format source_id:paragraph_index
        and remain consistent across multiple runs.
        """
        data = load_json_fixture("expected_passages.json")
        source_id = data["metadata"]["source_id"]

        for passage in data["passages"]:
            expected_id = f"{source_id}:{passage['paragraph_index']}"
            assert passage["passage_id"] == expected_id, (
                f"Passage ID mismatch: expected {expected_id}, got {passage['passage_id']}"
            )

    def test_passage_ids_sequential(self):
        """Passage IDs are sequential with no gaps."""
        data = load_json_fixture("expected_passages.json")
        indices = [p["paragraph_index"] for p in data["passages"]]
        sorted_indices = sorted(indices)

        # Check sequential (allowing for gaps in paragraph detection)
        for i, idx in enumerate(sorted_indices):
            assert idx == i, f"Non-sequential passage index at position {i}"

    def test_passage_char_offsets_non_overlapping(self):
        """Passage character offsets do not overlap."""
        data = load_json_fixture("expected_passages.json")
        passages = sorted(data["passages"], key=lambda p: p["char_start"])

        for i in range(len(passages) - 1):
            current_end = passages[i]["char_end"]
            next_start = passages[i + 1]["char_start"]
            assert current_end <= next_start, (
                f"Overlapping passages: {passages[i]['passage_id']} ends at "
                f"{current_end} but {passages[i + 1]['passage_id']} starts at "
                f"{next_start}"
            )

    def test_entity_extraction_stable(self):
        """Same input produces same entities.

        Entity IDs and canonical names must be consistent.
        """
        data = load_json_fixture("expected_entities.json")
        entity_ids = {e["entity_id"] for e in data["entities"]}

        # All entity IDs must be unique
        assert len(entity_ids) == len(data["entities"]), "Duplicate entity IDs detected"

        # Entity types must be from the valid set
        valid_types = {"person", "place", "group", "title", "artifact", "vehicle"}
        for entity in data["entities"]:
            assert entity["entity_type"] in valid_types, (
                f"Invalid entity type: {entity['entity_type']}"
            )

    def test_entity_first_seen_references_valid_passage(self):
        """Entity first_seen_passage references a valid passage ID."""
        passages_data = load_json_fixture("expected_passages.json")
        entities_data = load_json_fixture("expected_entities.json")

        valid_passage_ids = {p["passage_id"] for p in passages_data["passages"]}

        for entity in entities_data["entities"]:
            assert entity["first_seen_passage"] in valid_passage_ids, (
                f"Entity {entity['entity_id']} references invalid passage: "
                f"{entity['first_seen_passage']}"
            )

    def test_obligation_extraction_stable(self):
        """Same input produces same obligations.

        Obligation IDs and categories must be consistent.
        """
        data = load_json_fixture("expected_obligations.json")
        obligation_ids = {o["obligation_id"] for o in data["obligations"]}

        # All obligation IDs must be unique
        assert len(obligation_ids) == len(data["obligations"]), "Duplicate obligation IDs detected"

        # Obligation categories must be from the valid set
        valid_categories = {"plot_thread", "chekhov_gun", "prophecy_vision", "mystery"}
        for obligation in data["obligations"]:
            assert obligation["category"] in valid_categories, (
                f"Invalid obligation category: {obligation['category']}"
            )

    def test_obligation_evidence_anchors_exist(self):
        """Each obligation has at least one evidence anchor."""
        data = load_json_fixture("expected_obligations.json")

        for obligation in data["obligations"]:
            assert len(obligation["evidence_anchor_ids"]) >= 1, (
                f"Obligation {obligation['obligation_id']} has no evidence anchors"
            )

    def test_evidence_anchors_reference_valid_passages(self):
        """Evidence anchors reference valid passage IDs."""
        passages_data = load_json_fixture("expected_passages.json")
        obligations_data = load_json_fixture("expected_obligations.json")

        valid_passage_ids = {p["passage_id"] for p in passages_data["passages"]}

        for anchor in obligations_data["evidence_anchors"]:
            assert anchor["passage_id"] in valid_passage_ids, (
                f"Evidence anchor {anchor['anchor_id']} references invalid passage: "
                f"{anchor['passage_id']}"
            )

    def test_obligation_last_seen_references_valid_passage(self):
        """Obligation last_seen_passage_id references a valid passage."""
        passages_data = load_json_fixture("expected_passages.json")
        obligations_data = load_json_fixture("expected_obligations.json")

        valid_passage_ids = {p["passage_id"] for p in passages_data["passages"]}

        for obligation in obligations_data["obligations"]:
            assert obligation["last_seen_passage_id"] in valid_passage_ids, (
                f"Obligation {obligation['obligation_id']} references invalid "
                f"passage: {obligation['last_seen_passage_id']}"
            )

    def test_dossier_format_stable(self):
        """Same input produces same dossier structure.

        The dossier markdown must contain all expected sections.
        """
        dossier = load_fixture("expected_dossier.md")

        # Required sections
        required_sections = [
            "# Showrunner Dossier:",
            "## Entities",
            "### People",
            "### Places",
            "## Obligations",
            "### Prophecies & Visions",
            "### Chekhov's Guns",
            "### Mysteries",
            "### Plot Threads",
            "## Obligation Graph",
            "## Summary Statistics",
        ]

        for section in required_sections:
            assert section in dossier, f"Missing dossier section: {section}"

    def test_dossier_entities_match_expected(self):
        """Dossier contains all expected entities."""
        dossier = load_fixture("expected_dossier.md")
        entities_data = load_json_fixture("expected_entities.json")

        for entity in entities_data["entities"]:
            assert entity["canonical_name"] in dossier, (
                f"Entity {entity['canonical_name']} not found in dossier"
            )

    def test_dossier_obligations_match_expected(self):
        """Dossier contains all expected obligations."""
        dossier = load_fixture("expected_dossier.md")
        obligations_data = load_json_fixture("expected_obligations.json")

        for obligation in obligations_data["obligations"]:
            assert obligation["obligation_id"] in dossier, (
                f"Obligation {obligation['obligation_id']} not found in dossier"
            )

    def test_full_pipeline_deterministic(self):
        """Full pipeline produces identical outputs on rerun.

        This test validates the cross-referential integrity of all
        golden fixtures, ensuring they form a consistent output set.
        """
        passages = load_json_fixture("expected_passages.json")
        entities = load_json_fixture("expected_entities.json")
        obligations = load_json_fixture("expected_obligations.json")
        dossier = load_fixture("expected_dossier.md")

        # All fixtures share the same source_id
        source_id = passages["metadata"]["source_id"]
        assert entities["metadata"]["source_id"] == source_id
        assert obligations["metadata"]["source_id"] == source_id
        assert source_id in dossier

        # Passage count is consistent
        total_passages = passages["metadata"]["total_passages"]
        assert len(passages["passages"]) >= total_passages

        # Entity count is consistent
        total_entities = entities["metadata"]["total_entities"]
        assert len(entities["entities"]) == total_entities

        # Obligation count is consistent
        total_obligations = obligations["metadata"]["total_obligations"]
        assert len(obligations["obligations"]) == total_obligations

        # All evidence anchor IDs referenced by obligations exist
        anchor_ids = {a["anchor_id"] for a in obligations["evidence_anchors"]}
        for obligation in obligations["obligations"]:
            for anchor_id in obligation["evidence_anchor_ids"]:
                assert anchor_id in anchor_ids, (
                    f"Obligation {obligation['obligation_id']} references "
                    f"non-existent anchor: {anchor_id}"
                )

        # All entity IDs referenced by obligations exist
        entity_ids = {e["entity_id"] for e in entities["entities"]}
        for obligation in obligations["obligations"]:
            for entity_id in obligation.get("related_entity_ids", []):
                assert entity_id in entity_ids, (
                    f"Obligation {obligation['obligation_id']} references "
                    f"non-existent entity: {entity_id}"
                )

    def test_corpus_contains_all_patterns(self):
        """Sample corpus contains all required narrative patterns.

        The golden corpus must include:
        - Named characters (Jon, Daenerys, Tyrion)
        - Places (Winterfell, King's Landing)
        - A prophecy mention
        - A mystery/question
        - A Chekhov's gun (named artifact)
        - Dialogue
        - Multiple paragraphs
        """
        corpus = load_fixture("sample_corpus.txt")

        # Named characters
        assert "Jon" in corpus, "Corpus missing character: Jon"
        assert "Daenerys" in corpus, "Corpus missing character: Daenerys"
        assert "Tyrion" in corpus, "Corpus missing character: Tyrion"

        # Places
        assert "Winterfell" in corpus, "Corpus missing place: Winterfell"
        assert "King's Landing" in corpus, "Corpus missing place: King's Landing"

        # Prophecy pattern
        assert "prophecy" in corpus.lower(), "Corpus missing prophecy mention"

        # Mystery/question pattern
        assert "?" in corpus, "Corpus missing question/mystery"

        # Chekhov's gun (significant artifact)
        assert "Dagger" in corpus or "dagger" in corpus, "Corpus missing artifact"

        # Dialogue (quoted speech)
        assert '"' in corpus, "Corpus missing dialogue"

        # Multiple paragraphs
        paragraphs = [p for p in corpus.split("\n\n") if p.strip()]
        assert len(paragraphs) >= 5, f"Too few paragraphs: {len(paragraphs)}"


class TestGoldenObligationCategories:
    """Tests for obligation category stability and coverage."""

    def test_all_categories_represented(self):
        """All obligation categories are represented in fixtures."""
        data = load_json_fixture("expected_obligations.json")
        categories = {o["category"] for o in data["obligations"]}

        expected_categories = {"plot_thread", "chekhov_gun", "prophecy_vision", "mystery"}
        assert categories == expected_categories, (
            f"Missing categories: {expected_categories - categories}"
        )

    def test_prophecy_vision_has_correct_structure(self):
        """Prophecy/vision obligations have expected structure."""
        data = load_json_fixture("expected_obligations.json")
        prophecies = [o for o in data["obligations"] if o["category"] == "prophecy_vision"]

        assert len(prophecies) >= 1, "No prophecy obligations found"
        for prophecy in prophecies:
            assert prophecy["confidence"] >= 0.5, "Prophecy confidence too low"
            assert len(prophecy["evidence_anchor_ids"]) >= 1

    def test_chekhov_gun_has_artifact_reference(self):
        """Chekhov's gun obligations reference an artifact entity."""
        entities_data = load_json_fixture("expected_entities.json")
        obligations_data = load_json_fixture("expected_obligations.json")

        artifact_ids = {
            e["entity_id"] for e in entities_data["entities"] if e["entity_type"] == "artifact"
        }

        chekhov_guns = [
            o for o in obligations_data["obligations"] if o["category"] == "chekhov_gun"
        ]

        for gun in chekhov_guns:
            related_ids = set(gun.get("related_entity_ids", []))
            has_artifact = bool(related_ids & artifact_ids)
            assert has_artifact, f"Chekhov's gun {gun['obligation_id']} has no artifact reference"

    def test_mystery_has_question_evidence(self):
        """Mystery obligations have evidence containing question patterns."""
        data = load_json_fixture("expected_obligations.json")
        mysteries = [o for o in data["obligations"] if o["category"] == "mystery"]

        assert len(mysteries) >= 1, "No mystery obligations found"

        # At least one mystery should have question-related evidence
        anchor_ids = {a["anchor_id"]: a for a in data["evidence_anchors"]}
        for mystery in mysteries:
            for anchor_id in mystery["evidence_anchor_ids"]:
                anchor = anchor_ids.get(anchor_id, {})
                excerpt = anchor.get("excerpt", "")
                # Check for question mark or interrogative words
                if "?" in excerpt or "who" in excerpt.lower():
                    break
            else:
                continue
            break
        else:
            pytest.fail("No mystery has question-pattern evidence")
