"""Tests for InputAdapter module.

TDD tests for FileInputAdapter, FolderInputAdapter, and create_adapter factory.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from showrunner.contracts import DocumentUnit
from showrunner.adapters.input_adapter import (
    FileInputAdapter,
    FolderInputAdapter,
    create_adapter,
    InputAdapter,
    parse_filename_metadata,
)


# =============================================================================
# Filename Parsing Tests
# =============================================================================


class TestParseFilenameMetadata:
    """Tests for metadata extraction from filenames."""

    def test_parse_filename_metadata_book_chapter_name_pattern(self) -> None:
        """Parse book1_chapter01_Bran.txt format."""
        book_label, chapter_label = parse_filename_metadata("book1_chapter01_Bran.txt")
        assert book_label == "book1"
        assert chapter_label == "chapter01_Bran"

    def test_parse_filename_metadata_chapter_only_pattern(self) -> None:
        """Parse chapter_01.txt format without book label."""
        book_label, chapter_label = parse_filename_metadata("chapter_01.txt")
        assert book_label is None
        assert chapter_label == "chapter_01"

    def test_parse_filename_metadata_simple_name(self) -> None:
        """Parse prologue.txt as chapter_label only."""
        book_label, chapter_label = parse_filename_metadata("prologue.txt")
        assert book_label is None
        assert chapter_label == "prologue"

    def test_parse_filename_metadata_book_chapter_numeric(self) -> None:
        """Parse book2_chapter05.txt format."""
        book_label, chapter_label = parse_filename_metadata("book2_chapter05.txt")
        assert book_label == "book2"
        assert chapter_label == "chapter05"

    def test_parse_filename_metadata_book_only_no_chapter(self) -> None:
        """Parse book3_intro.txt where second part is not a chapter."""
        book_label, chapter_label = parse_filename_metadata("book3_intro.txt")
        assert book_label == "book3"
        assert chapter_label == "intro"

    def test_parse_filename_metadata_multiple_underscores(self) -> None:
        """Parse book1_chapter02_the_wall.txt with multiple underscores."""
        book_label, chapter_label = parse_filename_metadata(
            "book1_chapter02_the_wall.txt"
        )
        assert book_label == "book1"
        assert chapter_label == "chapter02_the_wall"

    def test_parse_filename_metadata_no_extension(self) -> None:
        """Parse filename without extension."""
        book_label, chapter_label = parse_filename_metadata("chapter_01")
        assert book_label is None
        assert chapter_label == "chapter_01"


# =============================================================================
# FileInputAdapter Tests
# =============================================================================


class TestFileInputAdapter:
    """Tests for FileInputAdapter single-file loading."""

    def test_load_single_file_returns_list_of_one_document_unit(self) -> None:
        """Loading a single file returns exactly one DocumentUnit."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, world!", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert len(result) == 1
            assert isinstance(result[0], DocumentUnit)

    def test_load_single_file_captures_raw_text_content(self) -> None:
        """File content is captured in raw_text field."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "story.txt"
            content = "Once upon a time, there was a brave knight."
            test_file.write_text(content, encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text == content

    def test_load_single_file_sets_source_path(self) -> None:
        """Source path is set to the file path."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter.txt"
            test_file.write_text("Content here", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].source_path == str(test_file)

    def test_load_single_file_sets_source_id_from_stem(self) -> None:
        """Source ID is derived from filename stem."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "prologue.txt"
            test_file.write_text("In the beginning...", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].source_id == "prologue"

    def test_load_single_file_order_hint_is_zero(self) -> None:
        """Single file always has order_hint of 0."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "only_chapter.txt"
            test_file.write_text("Content", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].order_hint == 0

    def test_load_single_file_extracts_chapter_label(self) -> None:
        """Chapter label is extracted from filename."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter_01.txt"
            test_file.write_text("Chapter content", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].chapter_label == "chapter_01"

    def test_load_single_file_extracts_book_and_chapter_labels(self) -> None:
        """Both book and chapter labels extracted from book_chapter pattern."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "book1_chapter05_Ned.txt"
            test_file.write_text("Ned's chapter", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].book_label == "book1"
            assert result[0].chapter_label == "chapter05_Ned"

    def test_load_nonexistent_file_raises_file_not_found_error(self) -> None:
        """Loading a non-existent file raises FileNotFoundError."""
        adapter = FileInputAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.load(Path("/nonexistent/path/to/file.txt"))

    def test_load_directory_raises_value_error(self) -> None:
        """FileInputAdapter raises ValueError when given a directory."""
        with TemporaryDirectory() as tmpdir:
            adapter = FileInputAdapter()
            with pytest.raises(ValueError, match="not a file"):
                adapter.load(Path(tmpdir))

    def test_load_file_handles_utf8_encoding(self) -> None:
        """UTF-8 encoded content is properly loaded."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "unicode.txt"
            content = "Caf\u00e9 with \u2014 em-dash and \u201csmart quotes\u201d"
            test_file.write_text(content, encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text == content

    def test_load_empty_file_returns_document_with_empty_text(self) -> None:
        """Empty files are valid and return empty raw_text."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "empty.txt"
            test_file.write_text("", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text == ""

    def test_load_markdown_file(self) -> None:
        """Markdown files are treated as plain text."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter.md"
            content = "# Title\nSome *markdown* content."
            test_file.write_text(content, encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text == content
            assert result[0].source_id == "chapter"

    def test_load_markdown_extension_file(self) -> None:
        """Markdown files with .markdown extension are supported."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter.markdown"
            content = "Some markdown content."
            test_file.write_text(content, encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text == content
            assert result[0].source_id == "chapter"

    def test_load_docx_file_if_supported(self) -> None:
        """DOCX files are supported when python-docx is installed."""
        docx = pytest.importorskip("docx")

        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter.docx"
            document = docx.Document()
            document.add_paragraph("First line.")
            document.add_paragraph("Second line.")
            document.save(test_file)

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert "First line." in result[0].raw_text
            assert "Second line." in result[0].raw_text

    def test_load_pdf_file_if_supported(self) -> None:
        """PDF files are supported when pypdf is installed."""
        pytest.importorskip("pypdf")
        from pypdf import PdfWriter

        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "chapter.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            with test_file.open("wb") as f:
                writer.write(f)

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            assert result[0].raw_text.startswith("=== Page 1 ===")


# =============================================================================
# FolderInputAdapter Tests
# =============================================================================


class TestFolderInputAdapter:
    """Tests for FolderInputAdapter folder-of-files loading."""

    def test_load_folder_returns_list_of_document_units(self) -> None:
        """Loading a folder returns a list of DocumentUnits."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "chapter01.txt").write_text("First", encoding="utf-8")
            (folder / "chapter02.txt").write_text("Second", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert len(result) == 2
            assert all(isinstance(doc, DocumentUnit) for doc in result)

    def test_load_folder_maintains_deterministic_order_by_filename(self) -> None:
        """Documents are ordered deterministically by filename."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "chapter03.txt").write_text("Third", encoding="utf-8")
            (folder / "chapter01.txt").write_text("First", encoding="utf-8")
            (folder / "chapter02.txt").write_text("Second", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert result[0].source_id == "chapter01"
            assert result[1].source_id == "chapter02"
            assert result[2].source_id == "chapter03"

    def test_load_folder_sets_order_hint_sequentially(self) -> None:
        """Order hints are assigned 0, 1, 2, ... based on sorted order."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "b.txt").write_text("B", encoding="utf-8")
            (folder / "a.txt").write_text("A", encoding="utf-8")
            (folder / "c.txt").write_text("C", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert result[0].order_hint == 0
            assert result[0].source_id == "a"
            assert result[1].order_hint == 1
            assert result[1].source_id == "b"
            assert result[2].order_hint == 2
            assert result[2].source_id == "c"

    def test_load_folder_extracts_metadata_from_each_file(self) -> None:
        """Each file's metadata is extracted independently."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "book1_chapter01_Bran.txt").write_text("Bran", encoding="utf-8")
            (folder / "book1_chapter02_Catelyn.txt").write_text(
                "Catelyn", encoding="utf-8"
            )

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert result[0].book_label == "book1"
            assert result[0].chapter_label == "chapter01_Bran"
            assert result[1].book_label == "book1"
            assert result[1].chapter_label == "chapter02_Catelyn"

    def test_load_folder_ignores_non_text_files(self) -> None:
        """Unsupported files are ignored; supported extensions are loaded."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "chapter01.txt").write_text("Text file", encoding="utf-8")
            (folder / "notes.md").write_text("Markdown", encoding="utf-8")
            (folder / "data.json").write_text("{}", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert len(result) == 2
            assert result[0].source_id == "chapter01"
            assert result[1].source_id == "notes"

    def test_load_folder_ignores_subdirectories(self) -> None:
        """Subdirectories are not traversed or loaded."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "chapter01.txt").write_text("Root file", encoding="utf-8")
            subdir = folder / "subdir"
            subdir.mkdir()
            (subdir / "chapter02.txt").write_text("Nested file", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert len(result) == 1
            assert result[0].source_id == "chapter01"

    def test_load_folder_with_no_text_files_returns_empty_list(self) -> None:
        """Empty folder or folder with no supported files returns empty list."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "readme.json").write_text("Not supported", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert result == []

    def test_load_nonexistent_folder_raises_file_not_found_error(self) -> None:
        """Loading a non-existent folder raises FileNotFoundError."""
        adapter = FolderInputAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.load(Path("/nonexistent/folder"))

    def test_load_file_raises_value_error(self) -> None:
        """FolderInputAdapter raises ValueError when given a file."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content", encoding="utf-8")

            adapter = FolderInputAdapter()
            with pytest.raises(ValueError, match="not a directory"):
                adapter.load(test_file)

    def test_load_folder_sets_source_path_for_each_file(self) -> None:
        """Each DocumentUnit has its correct source_path."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            file1 = folder / "ch1.txt"
            file2 = folder / "ch2.txt"
            file1.write_text("One", encoding="utf-8")
            file2.write_text("Two", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            source_paths = {doc.source_path for doc in result}
            assert str(file1) in source_paths
            assert str(file2) in source_paths

    def test_load_folder_handles_mixed_book_patterns(self) -> None:
        """Folder with mixed filename patterns is handled correctly."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "book1_chapter01.txt").write_text("A", encoding="utf-8")
            (folder / "prologue.txt").write_text("B", encoding="utf-8")
            (folder / "chapter_02.txt").write_text("C", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            # Results sorted alphabetically: book1_chapter01, chapter_02, prologue
            assert len(result) == 3
            assert result[0].source_id == "book1_chapter01"
            assert result[0].book_label == "book1"
            assert result[1].source_id == "chapter_02"
            assert result[1].book_label is None
            assert result[2].source_id == "prologue"
            assert result[2].chapter_label == "prologue"


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestCreateAdapterFactory:
    """Tests for create_adapter factory function."""

    def test_create_adapter_returns_file_adapter_for_file(self) -> None:
        """Factory returns FileInputAdapter for file path."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content", encoding="utf-8")

            adapter = create_adapter(test_file)

            assert isinstance(adapter, FileInputAdapter)

    def test_create_adapter_returns_folder_adapter_for_directory(self) -> None:
        """Factory returns FolderInputAdapter for directory path."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)

            adapter = create_adapter(folder)

            assert isinstance(adapter, FolderInputAdapter)

    def test_create_adapter_raises_for_nonexistent_path(self) -> None:
        """Factory raises FileNotFoundError for non-existent path."""
        with pytest.raises(FileNotFoundError):
            create_adapter(Path("/nonexistent/path"))

    def test_create_adapter_result_implements_input_adapter_protocol(self) -> None:
        """Factory result satisfies InputAdapter protocol."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content", encoding="utf-8")

            adapter = create_adapter(test_file)

            # Protocol check - has load method with correct signature
            assert hasattr(adapter, "load")
            assert callable(adapter.load)


# =============================================================================
# Integration Tests
# =============================================================================


class TestInputAdapterIntegration:
    """Integration tests for the complete adapter workflow."""

    def test_file_adapter_produces_valid_document_unit(self) -> None:
        """FileInputAdapter produces DocumentUnits that pass Pydantic validation."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "book1_chapter01_Bran.txt"
            test_file.write_text("Bran saw something.", encoding="utf-8")

            adapter = FileInputAdapter()
            result = adapter.load(test_file)

            # This implicitly tests Pydantic validation
            doc = result[0]
            assert doc.source_id == "book1_chapter01_Bran"
            assert doc.source_path == str(test_file)
            assert doc.order_hint == 0
            assert doc.raw_text == "Bran saw something."
            assert doc.book_label == "book1"
            assert doc.chapter_label == "chapter01_Bran"

    def test_folder_adapter_produces_valid_document_units(self) -> None:
        """FolderInputAdapter produces valid DocumentUnits for all files."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "book1_chapter01_Bran.txt").write_text("Bran", encoding="utf-8")
            (folder / "book1_chapter02_Cat.txt").write_text("Catelyn", encoding="utf-8")

            adapter = FolderInputAdapter()
            result = adapter.load(folder)

            assert len(result) == 2
            # Verify all required fields are populated
            for i, doc in enumerate(result):
                assert doc.source_id
                assert doc.source_path
                assert doc.order_hint == i
                assert doc.raw_text
                assert doc.book_label == "book1"

    def test_factory_and_adapters_work_end_to_end(self) -> None:
        """Complete workflow from factory to document loading."""
        with TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "chapters"
            folder.mkdir()
            (folder / "ch1.txt").write_text("Chapter 1", encoding="utf-8")
            (folder / "ch2.txt").write_text("Chapter 2", encoding="utf-8")

            # Use factory to get adapter
            adapter = create_adapter(folder)
            result = adapter.load(folder)

            assert len(result) == 2
            assert result[0].raw_text == "Chapter 1"
            assert result[1].raw_text == "Chapter 2"
