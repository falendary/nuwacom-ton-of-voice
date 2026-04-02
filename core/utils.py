"""
Shared upload validation utilities.

Used by both core.views (template UI) and core.api_views (REST API)
to keep validation logic in one place.
"""

from typing import Any

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "docx", "txt", "png"})
MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024  # 20 MB
MAX_FILENAME_LENGTH: int = 255

# Magic-byte prefixes for binary formats.
MIME_MAGIC: dict[str, bytes] = {
    "pdf": b"%PDF",
    "png": b"\x89PNG",
    "docx": b"PK",  # DOCX is a ZIP archive
}


def validate_file(file: Any) -> tuple[str, str | None]:
    """Validate a file upload: extension, size, filename length, and magic bytes.

    Parameters
    ----------
    file:
        An uploaded file object (``InMemoryUploadedFile`` or ``TemporaryUploadedFile``).

    Returns
    -------
    tuple[str, str | None]
        ``(extension, error_message)``. ``error_message`` is ``None`` when the file is valid.
    """
    name: str = getattr(file, "name", "") or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext not in ALLOWED_EXTENSIONS:
        return ext, f"Unsupported file type '.{ext}'. Accepted: pdf, docx, txt, png."

    if file.size > MAX_UPLOAD_BYTES:
        return ext, "File exceeds the 20 MB size limit."

    if len(name) > MAX_FILENAME_LENGTH:
        return ext, f"Filename is too long (max {MAX_FILENAME_LENGTH} characters)."

    if ext in MIME_MAGIC:
        header = file.read(8)
        file.seek(0)
        if not header.startswith(MIME_MAGIC[ext]):
            return ext, f"File content does not match the '{ext}' format."

    return ext, None
