"""
Text extraction service.

Accepts an uploaded file object and its type string, returns the extracted
plain text (capped at MAX_CHARS) and a flag indicating whether truncation occurred.

Supported file types: txt, pdf, docx, png
"""

import logging
from typing import IO

import pytesseract
from PIL import Image
from docx import Document as DocxDocument
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_CHARS = 12_000


def extract_text(file: IO[bytes], file_type: str) -> tuple[str, bool]:
    """Extract plain text from an uploaded file.

    Parameters
    ----------
    file:
        A file-like object opened in binary mode (e.g. ``InMemoryUploadedFile``).
    file_type:
        One of ``"txt"``, ``"pdf"``, ``"docx"``, ``"png"``.

    Returns
    -------
    tuple[str, bool]
        ``(extracted_text, was_truncated)`` — ``was_truncated`` is ``True`` when
        the raw text exceeded ``MAX_CHARS`` and was trimmed.

    Raises
    ------
    ValueError
        If the file type is unsupported, the file is empty, or the file cannot
        be parsed (corrupt / unreadable).
    """
    file_type = file_type.lower().lstrip(".")

    if file_type == "txt":
        raw = _extract_txt(file)
    elif file_type == "pdf":
        raw = _extract_pdf(file)
    elif file_type == "docx":
        raw = _extract_docx(file)
    elif file_type == "png":
        raw = _extract_png(file)
    else:
        raise ValueError(f"Unsupported file type: '{file_type}'. Expected one of: txt, pdf, docx, png.")

    raw = raw.strip()
    if not raw:
        raise ValueError("The file appears to be empty or contains no extractable text.")

    if len(raw) > MAX_CHARS:
        logger.warning("Extracted text truncated from %d to %d characters.", len(raw), MAX_CHARS)
        return raw[:MAX_CHARS], True

    return raw, False


# ---------------------------------------------------------------------------
# Private extractors
# ---------------------------------------------------------------------------

def _extract_txt(file: IO[bytes]) -> str:
    try:
        return file.read().decode("utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise ValueError(f"Could not read text file: {exc}") from exc


def _extract_pdf(file: IO[bytes]) -> str:
    try:
        reader = PdfReader(file)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception as exc:
        raise ValueError(f"Could not read PDF file: {exc}") from exc


def _extract_docx(file: IO[bytes]) -> str:
    try:
        doc = DocxDocument(file)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:
        raise ValueError(f"Could not read DOCX file: {exc}") from exc


def _extract_png(file: IO[bytes]) -> str:
    try:
        image = Image.open(file)
        return pytesseract.image_to_string(image)
    except Exception as exc:
        raise ValueError(f"Could not read PNG file: {exc}") from exc
