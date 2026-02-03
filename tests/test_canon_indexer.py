"""Tests for CanonIndexer module.

TDD tests covering:
- Paragraph segmentation with various inputs
- Passage ID generation and stability
- SQLite index building
- JSONL export
- Edge cases and error handling
"""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

import pytest

from showrunner.contracts import DocumentUnit, PassageRecord
from showrunner.indexers.canon_indexer import CanonIndexer

if TYPE_CHECKING:
    from pathlib import Path

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def indexer() -> CanonIndexer:
    """Create a default CanonIndexer instance."""
    return CanonIndexer()


@pytest.fixture
def sample_document() -> DocumentUnit:
    """Create a sample document with multiple paragraphs."""
    return DocumentUnit(
        source_id="book1_ch1",
        source_path="/path/to/book1/ch1.txt",
        order_hint=0,
        raw_text="First paragraph here.\n\nSecond paragraph follows.\n\nThird paragraph ends.",
        book_label="Book One",
        chapter_label="Chapter 1",
    )


@pytest.fixture
def multi_document_corpus() -> list[DocumentUnit]:
    """Create a corpus with multiple documents."""
    return [
        DocumentUnit(
            source_id="book1_ch1",
            source_path="/path/to/book1/ch1.txt",
            order_hint=0,
            raw_text="Chapter one intro.\n\nChapter one body.",
            book_label="Book One",
            chapter_label="Chapter 1",
        ),
        DocumentUnit(
            source_id="book1_ch2",
            source_path="/path/to/book1/ch2.txt",
            order_hint=1,
            raw_text="Chapter two intro.\n\nChapter two body.\n\nChapter two conclusion.",
            book_label="Book One",
            chapter_label="Chapter 2",
        ),
    ]


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test_passages.db"


@pytest.fixture
def temp_jsonl_path(tmp_path: Path) -> Path:
    """Provide a temporary JSONL output path."""
    return tmp_path / "passages.jsonl"


# =============================================================================
# Tests: Initialization
# =============================================================================


class TestCanonIndexerInit:
    """Test CanonIndexer initialization."""

    def test_init_default_version_returns_1_0_0(self) -> None:
        """Default segmentation version should be 1.0.0."""
        indexer = CanonIndexer()
        assert indexer.segmentation_version == "1.0.0"

    def test_init_custom_version_stores_version(self) -> None:
        """Custom segmentation version should be stored."""
        indexer = CanonIndexer(segmentation_version="2.0.0")
        assert indexer.segmentation_version == "2.0.0"


# =============================================================================
# Tests: Paragraph Segmentation
# =============================================================================


class TestSegmentParagraphs:
    """Test the segment_paragraphs method."""

    def test_segment_paragraphs_simple_double_newline_splits_correctly(
        self, indexer: CanonIndexer
    ) -> None:
        """Double newlines should split paragraphs."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="Para one.\n\nPara two.",
        )
        passages = indexer.segment_paragraphs(doc)

        assert len(passages) == 2
        assert passages[0].text == "Para one."
        assert passages[1].text == "Para two."

    def test_segment_paragraphs_preserves_paragraph_order(
        self, indexer: CanonIndexer, sample_document: DocumentUnit
    ) -> None:
        """Paragraphs should maintain original order."""
        passages = indexer.segment_paragraphs(sample_document)

        assert len(passages) == 3
        assert passages[0].paragraph_index == 0
        assert passages[1].paragraph_index == 1
        assert passages[2].paragraph_index == 2

    def test_segment_paragraphs_generates_correct_passage_ids(
        self, indexer: CanonIndexer, sample_document: DocumentUnit
    ) -> None:
        """Passage IDs should follow {source_id}:{paragraph_index} format."""
        passages = indexer.segment_paragraphs(sample_document)

        assert passages[0].passage_id == "book1_ch1:0"
        assert passages[1].passage_id == "book1_ch1:1"
        assert passages[2].passage_id == "book1_ch1:2"

    def test_segment_paragraphs_tracks_char_offsets_correctly(self, indexer: CanonIndexer) -> None:
        """Character offsets should accurately reflect positions."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="First.\n\nSecond.",
        )
        passages = indexer.segment_paragraphs(doc)

        # "First." is at positions 0-6, then "\n\n", then "Second." at 8-15
        assert passages[0].char_start == 0
        assert passages[0].char_end == 6
        assert passages[1].char_start == 8
        assert passages[1].char_end == 15

    def test_segment_paragraphs_source_id_matches_document(
        self, indexer: CanonIndexer, sample_document: DocumentUnit
    ) -> None:
        """All passages should reference the source document ID."""
        passages = indexer.segment_paragraphs(sample_document)

        for passage in passages:
            assert passage.source_id == sample_document.source_id

    def test_segment_paragraphs_returns_passage_records(
        self, indexer: CanonIndexer, sample_document: DocumentUnit
    ) -> None:
        """Should return list of PassageRecord instances."""
        passages = indexer.segment_paragraphs(sample_document)

        assert all(isinstance(p, PassageRecord) for p in passages)


# =============================================================================
# Tests: Edge Cases
# =============================================================================


class TestSegmentParagraphsEdgeCases:
    """Test edge cases in paragraph segmentation."""

    def test_segment_paragraphs_empty_text_returns_empty_list(self, indexer: CanonIndexer) -> None:
        """Empty document should return empty list."""
        doc = DocumentUnit(
            source_id="empty",
            source_path="/empty.txt",
            order_hint=0,
            raw_text="",
        )
        passages = indexer.segment_paragraphs(doc)

        assert passages == []

    def test_segment_paragraphs_whitespace_only_returns_empty_list(
        self, indexer: CanonIndexer
    ) -> None:
        """Whitespace-only document should return empty list."""
        doc = DocumentUnit(
            source_id="whitespace",
            source_path="/whitespace.txt",
            order_hint=0,
            raw_text="   \n\n   \n\n   ",
        )
        passages = indexer.segment_paragraphs(doc)

        assert passages == []

    def test_segment_paragraphs_single_paragraph_no_splits(self, indexer: CanonIndexer) -> None:
        """Single paragraph without splits returns one passage."""
        doc = DocumentUnit(
            source_id="single",
            source_path="/single.txt",
            order_hint=0,
            raw_text="Just one paragraph with no double newlines.",
        )
        passages = indexer.segment_paragraphs(doc)

        assert len(passages) == 1
        assert passages[0].text == "Just one paragraph with no double newlines."
        assert passages[0].passage_id == "single:0"

    def test_segment_paragraphs_strips_leading_trailing_whitespace(
        self, indexer: CanonIndexer
    ) -> None:
        """Leading/trailing whitespace should be stripped from passages."""
        doc = DocumentUnit(
            source_id="padded",
            source_path="/padded.txt",
            order_hint=0,
            raw_text="  First with spaces.  \n\n  Second with spaces.  ",
        )
        passages = indexer.segment_paragraphs(doc)

        assert len(passages) == 2
        assert passages[0].text == "First with spaces."
        assert passages[1].text == "Second with spaces."

    def test_segment_paragraphs_skips_empty_paragraphs(self, indexer: CanonIndexer) -> None:
        """Empty paragraphs between content should be skipped."""
        doc = DocumentUnit(
            source_id="gaps",
            source_path="/gaps.txt",
            order_hint=0,
            raw_text="First.\n\n\n\nSecond.",
        )
        passages = indexer.segment_paragraphs(doc)

        # Should only have 2 passages, not 3 (no empty one in middle)
        assert len(passages) == 2
        assert passages[0].text == "First."
        assert passages[1].text == "Second."

    def test_segment_paragraphs_handles_triple_newlines(self, indexer: CanonIndexer) -> None:
        """Triple newlines should also split paragraphs."""
        doc = DocumentUnit(
            source_id="triple",
            source_path="/triple.txt",
            order_hint=0,
            raw_text="First.\n\n\nSecond.",
        )
        passages = indexer.segment_paragraphs(doc)

        assert len(passages) == 2

    def test_segment_paragraphs_handles_mixed_line_endings(self, indexer: CanonIndexer) -> None:
        """Mixed line endings (CRLF) should be handled."""
        doc = DocumentUnit(
            source_id="crlf",
            source_path="/crlf.txt",
            order_hint=0,
            raw_text="First.\r\n\r\nSecond.",
        )
        passages = indexer.segment_paragraphs(doc)

        assert len(passages) == 2
        assert passages[0].text == "First."
        assert passages[1].text == "Second."


# =============================================================================
# Tests: Determinism and Stability
# =============================================================================


class TestDeterminism:
    """Test that segmentation is deterministic and IDs are stable."""

    def test_segment_paragraphs_is_deterministic_across_calls(
        self, indexer: CanonIndexer, sample_document: DocumentUnit
    ) -> None:
        """Same document should produce identical results on multiple calls."""
        passages1 = indexer.segment_paragraphs(sample_document)
        passages2 = indexer.segment_paragraphs(sample_document)

        assert len(passages1) == len(passages2)
        for p1, p2 in zip(passages1, passages2, strict=True):
            assert p1.passage_id == p2.passage_id
            assert p1.text == p2.text
            assert p1.char_start == p2.char_start
            assert p1.char_end == p2.char_end

    def test_passage_ids_stable_across_indexer_instances(
        self, sample_document: DocumentUnit
    ) -> None:
        """Different indexer instances should produce same IDs."""
        indexer1 = CanonIndexer()
        indexer2 = CanonIndexer()

        passages1 = indexer1.segment_paragraphs(sample_document)
        passages2 = indexer2.segment_paragraphs(sample_document)

        assert [p.passage_id for p in passages1] == [p.passage_id for p in passages2]

    def test_index_is_deterministic_across_runs(
        self,
        indexer: CanonIndexer,
        multi_document_corpus: list[DocumentUnit],
        tmp_path: Path,
    ) -> None:
        """Indexing should be deterministic across runs."""
        db_path1 = tmp_path / "db1.db"
        db_path2 = tmp_path / "db2.db"

        passages1, conn1 = indexer.index(multi_document_corpus, db_path1)
        passages2, conn2 = indexer.index(multi_document_corpus, db_path2)

        conn1.close()
        conn2.close()

        assert len(passages1) == len(passages2)
        for p1, p2 in zip(passages1, passages2, strict=True):
            assert p1.passage_id == p2.passage_id


# =============================================================================
# Tests: SQLite Index
# =============================================================================


class TestIndexMethod:
    """Test the index method and SQLite database creation."""

    def test_index_creates_database_file(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """Index should create SQLite database file."""
        passages, conn = indexer.index([sample_document], temp_db_path)
        conn.close()

        assert temp_db_path.exists()

    def test_index_returns_passages_and_connection(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """Index should return tuple of passages and connection."""
        result = indexer.index([sample_document], temp_db_path)

        assert isinstance(result, tuple)
        assert len(result) == 2
        passages, conn = result
        assert isinstance(passages, list)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_index_creates_passages_table(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """Index should create passages table with correct schema."""
        passages, conn = indexer.index([sample_document], temp_db_path)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='passages'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_index_creates_source_index(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """Index should create idx_source index."""
        passages, conn = indexer.index([sample_document], temp_db_path)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_source'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_index_creates_order_index(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """Index should create idx_order index."""
        passages, conn = indexer.index([sample_document], temp_db_path)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_order'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_index_inserts_all_passages(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_db_path: Path,
    ) -> None:
        """All passages should be inserted into database."""
        passages, conn = indexer.index([sample_document], temp_db_path)

        cursor = conn.execute("SELECT COUNT(*) FROM passages")
        count = cursor.fetchone()[0]

        assert count == len(passages)
        conn.close()

    def test_index_stores_correct_passage_data(
        self,
        indexer: CanonIndexer,
        temp_db_path: Path,
    ) -> None:
        """Stored passage data should match input."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="Hello world.",
        )
        passages, conn = indexer.index([doc], temp_db_path)

        cursor = conn.execute(
            "SELECT passage_id, source_id, paragraph_index, text, char_start, char_end "
            "FROM passages WHERE passage_id = ?",
            ("test:0",),
        )
        row = cursor.fetchone()

        assert row[0] == "test:0"  # passage_id
        assert row[1] == "test"  # source_id
        assert row[2] == 0  # paragraph_index
        assert row[3] == "Hello world."  # text
        assert row[4] == 0  # char_start
        assert row[5] == 12  # char_end
        conn.close()

    def test_index_multiple_documents_stores_all(
        self,
        indexer: CanonIndexer,
        multi_document_corpus: list[DocumentUnit],
        temp_db_path: Path,
    ) -> None:
        """Multiple documents should all be indexed."""
        passages, conn = indexer.index(multi_document_corpus, temp_db_path)

        cursor = conn.execute("SELECT DISTINCT source_id FROM passages")
        source_ids = {row[0] for row in cursor.fetchall()}

        assert source_ids == {"book1_ch1", "book1_ch2"}
        conn.close()

    def test_index_empty_list_returns_empty_passages(
        self,
        indexer: CanonIndexer,
        temp_db_path: Path,
    ) -> None:
        """Empty document list should return empty passages."""
        passages, conn = indexer.index([], temp_db_path)

        assert passages == []
        cursor = conn.execute("SELECT COUNT(*) FROM passages")
        assert cursor.fetchone()[0] == 0
        conn.close()

    def test_index_can_query_by_source_id(
        self,
        indexer: CanonIndexer,
        multi_document_corpus: list[DocumentUnit],
        temp_db_path: Path,
    ) -> None:
        """Should be able to query passages by source_id."""
        passages, conn = indexer.index(multi_document_corpus, temp_db_path)

        cursor = conn.execute(
            "SELECT passage_id FROM passages WHERE source_id = ? ORDER BY paragraph_index",
            ("book1_ch2",),
        )
        results = cursor.fetchall()

        assert len(results) == 3  # Chapter 2 has 3 paragraphs
        assert results[0][0] == "book1_ch2:0"
        assert results[1][0] == "book1_ch2:1"
        assert results[2][0] == "book1_ch2:2"
        conn.close()


# =============================================================================
# Tests: JSONL Export
# =============================================================================


class TestWritePassagesJsonl:
    """Test the write_passages_jsonl method."""

    def test_write_passages_jsonl_creates_file(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_jsonl_path: Path,
    ) -> None:
        """JSONL file should be created."""
        passages = indexer.segment_paragraphs(sample_document)
        indexer.write_passages_jsonl(passages, temp_jsonl_path)

        assert temp_jsonl_path.exists()

    def test_write_passages_jsonl_correct_line_count(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_jsonl_path: Path,
    ) -> None:
        """JSONL should have one line per passage."""
        passages = indexer.segment_paragraphs(sample_document)
        indexer.write_passages_jsonl(passages, temp_jsonl_path)

        lines = temp_jsonl_path.read_text().strip().split("\n")
        assert len(lines) == len(passages)

    def test_write_passages_jsonl_valid_json_per_line(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        temp_jsonl_path: Path,
    ) -> None:
        """Each line should be valid JSON."""
        passages = indexer.segment_paragraphs(sample_document)
        indexer.write_passages_jsonl(passages, temp_jsonl_path)

        lines = temp_jsonl_path.read_text().strip().split("\n")
        for line in lines:
            parsed = json.loads(line)  # Should not raise
            assert isinstance(parsed, dict)

    def test_write_passages_jsonl_contains_all_fields(
        self,
        indexer: CanonIndexer,
        temp_jsonl_path: Path,
    ) -> None:
        """Each JSON object should contain all PassageRecord fields."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="Single paragraph.",
        )
        passages = indexer.segment_paragraphs(doc)
        indexer.write_passages_jsonl(passages, temp_jsonl_path)

        line = temp_jsonl_path.read_text().strip()
        parsed = json.loads(line)

        expected_fields = {
            "passage_id",
            "source_id",
            "paragraph_index",
            "text",
            "char_start",
            "char_end",
        }
        assert set(parsed.keys()) == expected_fields

    def test_write_passages_jsonl_correct_values(
        self,
        indexer: CanonIndexer,
        temp_jsonl_path: Path,
    ) -> None:
        """JSON values should match passage data."""
        doc = DocumentUnit(
            source_id="book1",
            source_path="/book1.txt",
            order_hint=0,
            raw_text="Test content.",
        )
        passages = indexer.segment_paragraphs(doc)
        indexer.write_passages_jsonl(passages, temp_jsonl_path)

        line = temp_jsonl_path.read_text().strip()
        parsed = json.loads(line)

        assert parsed["passage_id"] == "book1:0"
        assert parsed["source_id"] == "book1"
        assert parsed["paragraph_index"] == 0
        assert parsed["text"] == "Test content."
        assert parsed["char_start"] == 0
        assert parsed["char_end"] == 13

    def test_write_passages_jsonl_empty_list_creates_empty_file(
        self,
        indexer: CanonIndexer,
        temp_jsonl_path: Path,
    ) -> None:
        """Empty passages list should create empty file."""
        indexer.write_passages_jsonl([], temp_jsonl_path)

        assert temp_jsonl_path.exists()
        assert temp_jsonl_path.read_text() == ""


# =============================================================================
# Tests: Segmentation Version
# =============================================================================


class TestSegmentationVersion:
    """Test segmentation version tracking."""

    def test_segmentation_version_accessible(self) -> None:
        """Segmentation version should be accessible."""
        indexer = CanonIndexer(segmentation_version="1.2.3")
        assert indexer.segmentation_version == "1.2.3"

    def test_different_versions_same_algorithm_for_now(self) -> None:
        """Different versions should produce same results in MVP."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="Para one.\n\nPara two.",
        )
        indexer_v1 = CanonIndexer(segmentation_version="1.0.0")
        indexer_v2 = CanonIndexer(segmentation_version="2.0.0")

        passages_v1 = indexer_v1.segment_paragraphs(doc)
        passages_v2 = indexer_v2.segment_paragraphs(doc)

        # In MVP, versions don't change algorithm
        assert len(passages_v1) == len(passages_v2)


# =============================================================================
# Tests: Integration
# =============================================================================


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow_segment_index_export(
        self,
        indexer: CanonIndexer,
        multi_document_corpus: list[DocumentUnit],
        tmp_path: Path,
    ) -> None:
        """Full workflow: segment, index, and export should work together."""
        db_path = tmp_path / "canon.db"
        jsonl_path = tmp_path / "passages.jsonl"

        # Index documents
        passages, conn = indexer.index(multi_document_corpus, db_path)

        # Export to JSONL
        indexer.write_passages_jsonl(passages, jsonl_path)

        # Verify database
        cursor = conn.execute("SELECT COUNT(*) FROM passages")
        db_count = cursor.fetchone()[0]
        conn.close()

        # Verify JSONL
        lines = jsonl_path.read_text().strip().split("\n")
        jsonl_count = len(lines)

        # All counts should match
        assert len(passages) == db_count == jsonl_count
        assert len(passages) == 5  # 2 paragraphs + 3 paragraphs

    def test_roundtrip_passage_data_preserved(
        self,
        indexer: CanonIndexer,
        sample_document: DocumentUnit,
        tmp_path: Path,
    ) -> None:
        """Passage data should be preserved through full workflow."""
        db_path = tmp_path / "canon.db"

        passages, conn = indexer.index([sample_document], db_path)

        # Query back from database
        cursor = conn.execute("SELECT passage_id, text FROM passages ORDER BY paragraph_index")
        db_passages = cursor.fetchall()
        conn.close()

        # Verify data matches
        for passage, db_row in zip(passages, db_passages, strict=True):
            assert passage.passage_id == db_row[0]
            assert passage.text == db_row[1]
