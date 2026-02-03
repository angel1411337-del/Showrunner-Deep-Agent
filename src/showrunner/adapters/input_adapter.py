"""Input adapters for loading documents from files and folders.

Provides unified interface for loading single files or folders of chapter files,
normalizing both to the same DocumentUnit model for downstream processing.
"""

from pathlib import Path
from typing import Protocol

from showrunner.contracts import DocumentUnit


class InputAdapter(Protocol):
    """Protocol for input adapters that load documents from various sources."""

    def load(self, source: Path) -> list[DocumentUnit]:
        """Load and normalize input to DocumentUnits.

        Args:
            source: Path to the input source (file or folder).

        Returns:
            List of DocumentUnit objects normalized from the source.
        """
        ...


def parse_filename_metadata(filename: str) -> tuple[str | None, str | None]:
    """Extract book and chapter labels from a filename.

    Parsing rules:
    - book1_chapter01_Bran.txt -> book_label="book1", chapter_label="chapter01_Bran"
    - chapter_01.txt -> book_label=None, chapter_label="chapter_01"
    - prologue.txt -> book_label=None, chapter_label="prologue"

    Args:
        filename: The filename (with or without extension) to parse.

    Returns:
        Tuple of (book_label, chapter_label). book_label may be None.
    """
    # Remove extension if present
    stem = Path(filename).stem if "." in filename else filename

    # Check for book_chapter pattern: book<N>_<rest>
    if stem.startswith("book") and "_" in stem:
        parts = stem.split("_", 1)
        book_part = parts[0]
        # Verify book_part matches pattern book<digits>
        if book_part[4:].isdigit() or len(book_part) > 4:
            book_label = book_part
            chapter_label = parts[1] if len(parts) > 1 else None
            return book_label, chapter_label

    # No book label - entire stem is chapter label
    return None, stem


class FileInputAdapter:
    """Adapter for loading a single file input.

    Loads a single text file and normalizes it to a DocumentUnit.
    """

    def load(self, source: Path) -> list[DocumentUnit]:
        """Load a single file and return as a list with one DocumentUnit.

        Args:
            source: Path to the text file to load.

        Returns:
            List containing a single DocumentUnit.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is a directory, not a file.
        """
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")

        if source.is_dir():
            raise ValueError(f"Path is not a file: {source}")

        raw_text = source.read_text(encoding="utf-8")
        book_label, chapter_label = parse_filename_metadata(source.name)

        doc = DocumentUnit(
            source_id=source.stem,
            source_path=str(source),
            order_hint=0,
            raw_text=raw_text,
            book_label=book_label,
            chapter_label=chapter_label,
        )

        return [doc]


class FolderInputAdapter:
    """Adapter for loading a folder of chapter files.

    Loads all .txt files from a folder, sorted alphabetically by filename,
    and normalizes each to a DocumentUnit with deterministic ordering.
    """

    def load(self, source: Path) -> list[DocumentUnit]:
        """Load all .txt files from a folder as DocumentUnits.

        Args:
            source: Path to the folder containing chapter files.

        Returns:
            List of DocumentUnit objects, one per .txt file,
            sorted alphabetically by filename with order_hint set accordingly.

        Raises:
            FileNotFoundError: If the folder does not exist.
            ValueError: If the path is a file, not a directory.
        """
        if not source.exists():
            raise FileNotFoundError(f"Folder not found: {source}")

        if source.is_file():
            raise ValueError(f"Path is not a directory: {source}")

        # Collect all .txt files, sorted alphabetically
        txt_files = sorted(
            [f for f in source.iterdir() if f.is_file() and f.suffix == ".txt"],
            key=lambda p: p.name,
        )

        documents: list[DocumentUnit] = []

        for order_hint, file_path in enumerate(txt_files):
            raw_text = file_path.read_text(encoding="utf-8")
            book_label, chapter_label = parse_filename_metadata(file_path.name)

            doc = DocumentUnit(
                source_id=file_path.stem,
                source_path=str(file_path),
                order_hint=order_hint,
                raw_text=raw_text,
                book_label=book_label,
                chapter_label=chapter_label,
            )
            documents.append(doc)

        return documents


def create_adapter(source: Path) -> InputAdapter:
    """Factory to create the appropriate adapter based on source type.

    Args:
        source: Path to the input source.

    Returns:
        FileInputAdapter if source is a file, FolderInputAdapter if directory.

    Raises:
        FileNotFoundError: If the source path does not exist.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source path not found: {source}")

    if source.is_file():
        return FileInputAdapter()
    else:
        return FolderInputAdapter()
