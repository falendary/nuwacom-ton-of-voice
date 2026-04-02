import io
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from core.services.extraction import MAX_CHARS, extract_text

FIXTURES = Path(__file__).parent / "fixtures"


def _open(filename: str) -> io.BytesIO:
    return io.BytesIO((FIXTURES / filename).read_bytes())


class TxtExtractionTests(TestCase):
    def test_extracts_text(self) -> None:
        text, truncated = extract_text(_open("sample.txt"), "txt")
        self.assertIn("sample text file", text)
        self.assertFalse(truncated)

    def test_extension_dot_prefix_accepted(self) -> None:
        text, truncated = extract_text(_open("sample.txt"), ".txt")
        self.assertFalse(truncated)
        self.assertTrue(text)


class PdfExtractionTests(TestCase):
    def test_extracts_text(self) -> None:
        text, truncated = extract_text(_open("sample.pdf"), "pdf")
        self.assertIn("sample PDF", text)
        self.assertFalse(truncated)


class DocxExtractionTests(TestCase):
    def test_extracts_text(self) -> None:
        text, truncated = extract_text(_open("sample.docx"), "docx")
        self.assertIn("sample DOCX", text)
        self.assertFalse(truncated)


class PngExtractionTests(TestCase):
    @patch("core.services.extraction.pytesseract.image_to_string", return_value="OCR extracted text")
    def test_extracts_text(self, _mock) -> None:
        text, truncated = extract_text(_open("sample.png"), "png")
        self.assertIn("OCR extracted text", text)
        self.assertFalse(truncated)

    @patch("core.services.extraction.pytesseract.image_to_string", side_effect=Exception("tesseract error"))
    def test_ocr_failure_raises_value_error(self, _mock) -> None:
        with self.assertRaises(ValueError) as ctx:
            extract_text(_open("sample.png"), "png")
        self.assertIn("Could not read PNG file", str(ctx.exception))


class TruncationTests(TestCase):
    def test_truncates_at_max_chars(self) -> None:
        text, truncated = extract_text(_open("long.txt"), "txt")
        self.assertEqual(len(text), MAX_CHARS)
        self.assertTrue(truncated)


class ErrorHandlingTests(TestCase):
    def test_unsupported_type_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            extract_text(io.BytesIO(b"data"), "xlsx")
        self.assertIn("Unsupported file type", str(ctx.exception))

    def test_empty_file_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_text(io.BytesIO(b""), "txt")

    def test_non_utf8_txt_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_text(io.BytesIO(b"\xff\xfe\x00invalid"), "txt")

    def test_corrupt_pdf_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_text(io.BytesIO(b"not a pdf"), "pdf")

    def test_corrupt_docx_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_text(io.BytesIO(b"not a docx"), "docx")
