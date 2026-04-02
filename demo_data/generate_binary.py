"""
Generate .pdf and .docx demo files from the corresponding .txt sources.

Uses only Python stdlib — no third-party dependencies required.

Run from the repository root:
    python demo_data/generate_binary.py
"""

import io
import os
import struct
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONVERSIONS = [
    (
        os.path.join(SCRIPT_DIR, "nuwacom", "product_page.txt"),
        os.path.join(SCRIPT_DIR, "nuwacom", "product_page.pdf"),
        os.path.join(SCRIPT_DIR, "nuwacom", "product_page.docx"),
    ),
    (
        os.path.join(SCRIPT_DIR, "apple", "feature_description.txt"),
        os.path.join(SCRIPT_DIR, "apple", "feature_description.pdf"),
        os.path.join(SCRIPT_DIR, "apple", "feature_description.docx"),
    ),
]


# ---------------------------------------------------------------------------
# Minimal valid PDF writer
# ---------------------------------------------------------------------------

def _pdf_escape(text: str) -> bytes:
    """Escape special PDF string characters and encode as Latin-1."""
    result = []
    for ch in text:
        if ch == "\\":
            result.append("\\\\")
        elif ch == "(":
            result.append("\\(")
        elif ch == ")":
            result.append("\\)")
        elif ch == "\r":
            result.append("\\r")
        elif ord(ch) > 127:
            # Replace non-Latin-1 characters with a space.
            result.append(" ")
        else:
            result.append(ch)
    return "".join(result).encode("latin-1")


def _build_pdf(text: str) -> bytes:
    """Return a minimal valid single-page PDF containing *text*."""
    # Split into lines; wrap long lines at 90 chars.
    raw_lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            raw_lines.append("")
            continue
        words = paragraph.split()
        current: list[str] = []
        for word in words:
            if sum(len(w) for w in current) + len(current) + len(word) > 90:
                raw_lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            raw_lines.append(" ".join(current))

    # Build the BT…ET content stream.
    leading = 14  # points between lines
    start_y = 750
    stream_parts = [b"BT\n/F1 11 Tf\n"]
    stream_parts.append(f"50 {start_y} Td\n{leading} TL\n".encode())
    for line in raw_lines:
        escaped = _pdf_escape(line)
        stream_parts.append(b"(" + escaped + b") '\n")
    stream_parts.append(b"ET\n")
    stream_data = b"".join(stream_parts)

    # Build PDF objects as byte strings.
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj\n"
    )
    obj4 = (
        b"4 0 obj\n"
        b"<< /Length " + str(len(stream_data)).encode() + b" >>\n"
        b"stream\n" + stream_data + b"endstream\n"
        b"endobj\n"
    )
    obj5 = (
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica\n"
        b"   /Encoding /WinAnsiEncoding >>\n"
        b"endobj\n"
    )

    header = b"%PDF-1.4\n"
    body = header
    offsets: list[int] = []

    for obj in (obj1, obj2, obj3, obj4, obj5):
        offsets.append(len(body))
        body += obj

    xref_offset = len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF\n"
    )
    return body + xref + trailer


# ---------------------------------------------------------------------------
# Minimal valid DOCX writer
# ---------------------------------------------------------------------------

_CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
"""

_DOC_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>
"""

_NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mo="http://schemas.microsoft.com/office/mac/office/2008/main" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:mv="urn:schemas-microsoft-com:mac:vml" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'mc:Ignorable="w14 wp14"'
)


def _xml_escape(text: str) -> str:
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _build_docx(text: str) -> bytes:
    """Return a minimal valid .docx file containing *text*."""
    paragraphs = text.splitlines()

    para_xml_parts = []
    for para in paragraphs:
        safe = _xml_escape(para)
        para_xml_parts.append(
            f"    <w:p><w:r><w:t xml:space=\"preserve\">{safe}</w:t></w:r></w:p>"
        )

    doc_xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<w:document {_NS}>\n'
        f'  <w:body>\n'
        + "\n".join(para_xml_parts)
        + "\n  </w:body>\n</w:document>\n"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/document.xml", doc_xml)
        zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    for txt_path, pdf_path, docx_path in CONVERSIONS:
        with open(txt_path, "r", encoding="utf-8") as fh:
            text = fh.read()

        pdf_bytes = _build_pdf(text)
        with open(pdf_path, "wb") as fh:
            fh.write(pdf_bytes)
        print(f"Created {os.path.relpath(pdf_path)}")

        docx_bytes = _build_docx(text)
        with open(docx_path, "wb") as fh:
            fh.write(docx_bytes)
        print(f"Created {os.path.relpath(docx_path)}")


if __name__ == "__main__":
    main()
