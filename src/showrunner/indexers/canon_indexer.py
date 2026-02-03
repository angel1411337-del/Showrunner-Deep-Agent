"""Canon Indexer for paragraph-level passage segmentation and indexing.

This module provides the CanonIndexer class which:
1. Normalizes input documents to stable paragraph passages
2. Builds SQLite lookup index by source/chapter/order_hint
3. Generates stable passage IDs in format {source_id}:{paragraph_index}
4. Tracks segmentation_version for migration support
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from showrunner.contracts import DocumentUnit, PassageRecord


class CanonIndexer:
    """Indexes canon documents into paragraph-level passages.

    Passage IDs are stable across reruns when text and segmentation rules
    remain unchanged. The segmentation_version allows tracking algorithm
    changes for migration support.
    """

    def __init__(self, segmentation_version: str = "1.0.0") -> None:
        """Initialize the CanonIndexer.

        Args:
            segmentation_version: Version string for the segmentation algorithm.
                Used for tracking and migration support.
        """
        self.segmentation_version = segmentation_version

    def segment_paragraphs(self, doc: DocumentUnit) -> list[PassageRecord]:
        """Split document into paragraph-level passages.

        Segmentation rules (MVP):
        - Split on double newlines (\\n\\n) or more
        - Handle CRLF line endings
        - Skip empty paragraphs
        - Strip leading/trailing whitespace from each paragraph
        - Track char_start/char_end offsets within source document

        Args:
            doc: The document to segment.

        Returns:
            List of PassageRecord instances, one per paragraph.
        """
        raw_text = doc.raw_text

        if not raw_text or not raw_text.strip():
            return []

        # Normalize CRLF to LF for consistent processing
        normalized_text = raw_text.replace("\r\n", "\n")

        # Split on double (or more) newlines
        # Pattern matches 2+ newlines (possibly with spaces between)
        paragraph_pattern = re.compile(r"\n\s*\n")

        passages: list[PassageRecord] = []
        paragraph_index = 0

        # Find all split positions
        parts = paragraph_pattern.split(normalized_text)

        # Track position for char offsets
        current_pos = 0

        for part in parts:
            # Find where this part starts in the original normalized text
            part_start = normalized_text.find(part, current_pos)

            # Strip whitespace for the actual text content
            stripped_text = part.strip()

            if stripped_text:
                # Calculate offsets in the original raw_text
                # Account for CRLF conversion if present
                char_start = self._find_original_offset(raw_text, normalized_text, part_start)

                # Find the actual content start/end within the part
                content_start_in_part = part.find(stripped_text[0]) if stripped_text else 0
                content_end_in_part = part.rfind(stripped_text[-1]) + 1 if stripped_text else 0

                # Adjust char_start to point to actual content
                actual_start = part_start + content_start_in_part
                actual_end = part_start + content_end_in_part

                # Convert back to original text offsets
                char_start = self._find_original_offset(raw_text, normalized_text, actual_start)
                char_end = self._find_original_offset(raw_text, normalized_text, actual_end)

                passage = PassageRecord(
                    passage_id=f"{doc.source_id}:{paragraph_index}",
                    source_id=doc.source_id,
                    paragraph_index=paragraph_index,
                    text=stripped_text,
                    char_start=char_start,
                    char_end=char_end,
                )
                passages.append(passage)
                paragraph_index += 1

            # Update current position
            current_pos = part_start + len(part)

        return passages

    def _find_original_offset(
        self,
        original: str,
        normalized: str,
        normalized_offset: int,
    ) -> int:
        """Convert offset in normalized text to offset in original text.

        Handles CRLF to LF conversion offset differences.

        Args:
            original: The original text with possible CRLF.
            normalized: The normalized text with LF only.
            normalized_offset: Offset in the normalized text.

        Returns:
            Corresponding offset in the original text.
        """
        if "\r\n" not in original:
            return normalized_offset

        # Count how many CRLF pairs occur before the normalized offset
        crlf_count = 0
        original_pos = 0
        normalized_pos = 0

        while normalized_pos < normalized_offset and original_pos < len(original):
            if (
                original_pos + 1 < len(original)
                and original[original_pos : original_pos + 2] == "\r\n"
            ):
                crlf_count += 1
                original_pos += 2
                normalized_pos += 1
            else:
                original_pos += 1
                normalized_pos += 1

        return normalized_offset + crlf_count

    def index(
        self,
        docs: list[DocumentUnit],
        db_path: Path,
    ) -> tuple[list[PassageRecord], sqlite3.Connection]:
        """Index all documents and build SQLite lookup.

        Creates a SQLite database with the passages table containing all
        segmented passages. Returns both the list of passages and an open
        connection to the database.

        Args:
            docs: List of documents to index.
            db_path: Path where the SQLite database should be created.

        Returns:
            Tuple of (list of all PassageRecords, open sqlite3.Connection).
        """
        # Segment all documents
        all_passages: list[PassageRecord] = []
        for doc in docs:
            passages = self.segment_paragraphs(doc)
            all_passages.extend(passages)

        # Create database
        conn = sqlite3.connect(db_path)
        self._create_schema(conn)

        # Insert passages
        self._insert_passages(conn, all_passages)

        return all_passages, conn

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create the database schema.

        Args:
            conn: Open database connection.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS passages (
                passage_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                paragraph_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                char_start INTEGER NOT NULL,
                char_end INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source ON passages(source_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_order ON passages(source_id, paragraph_index)
        """)

        conn.commit()

    def _insert_passages(
        self,
        conn: sqlite3.Connection,
        passages: list[PassageRecord],
    ) -> None:
        """Insert passages into the database.

        Args:
            conn: Open database connection.
            passages: List of passages to insert.
        """
        conn.executemany(
            """
            INSERT INTO passages (passage_id, source_id, paragraph_index, text, char_start, char_end)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.passage_id,
                    p.source_id,
                    p.paragraph_index,
                    p.text,
                    p.char_start,
                    p.char_end,
                )
                for p in passages
            ],
        )
        conn.commit()

    def write_passages_jsonl(
        self,
        passages: list[PassageRecord],
        output_path: Path,
    ) -> None:
        """Write passages to JSONL file.

        Each line contains one passage as a JSON object with all PassageRecord
        fields.

        Args:
            passages: List of passages to write.
            output_path: Path where the JSONL file should be created.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for passage in passages:
                json_line = json.dumps(
                    {
                        "passage_id": passage.passage_id,
                        "source_id": passage.source_id,
                        "paragraph_index": passage.paragraph_index,
                        "text": passage.text,
                        "char_start": passage.char_start,
                        "char_end": passage.char_end,
                    },
                    ensure_ascii=False,
                )
                f.write(json_line + "\n")

        # Handle empty list case - ensure file exists but is empty
        if not passages:
            output_path.write_text("")
