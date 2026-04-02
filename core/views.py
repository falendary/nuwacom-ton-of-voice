"""
Django template views for the Tone-of-Voice UI.

/            — upload.html  — upload documents, trigger extraction
/transform/  — transform.html — rewrite text in a brand's voice
"""

import logging
from typing import Any

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.models import Brand, Document
from core.services.claude import ClaudeServiceError, extract_signature, transform_text
from core.services.extraction import extract_text

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset({"pdf", "docx", "txt", "png"})
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB

MIME_MAGIC: dict[str, bytes] = {
    "pdf": b"%PDF",
    "png": b"\x89PNG",
    "docx": b"PK",
}


def _ctx(request, **extra: Any) -> dict[str, Any]:
    """Build base template context: all brands + any extra kwargs."""
    return {"brands": Brand.objects.all().order_by("name"), **extra}


# ---------------------------------------------------------------------------
# Upload view  /
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def upload_view(request):
    """Upload view — document upload, list, and signature extraction.

    GET  — render upload form with optional brand selection.
    POST — handle file upload, document deletion, or signature extraction.
    """
    brand_id = request.GET.get("brand") or request.POST.get("brand_id")
    brand = None
    if brand_id:
        brand = get_object_or_404(Brand, pk=brand_id)

    action = request.POST.get("action", "")

    if request.method == "POST":
        if action == "upload":
            return _handle_upload(request, brand)
        if action == "delete":
            return _handle_delete(request, brand)
        if action == "extract":
            return _handle_extract(request, brand)

    documents = brand.documents.all().order_by("-uploaded_at") if brand else []
    return render(request, "upload.html", _ctx(request, brand=brand, documents=documents))


def _handle_upload(request, brand):
    """Process a file upload for the given brand."""
    if brand is None:
        messages.error(request, "Select a brand before uploading.")
        return redirect("/")

    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, "No file selected.")
        return redirect(f"/?brand={brand.pk}")

    name = uploaded.name or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext not in ALLOWED_EXTENSIONS:
        messages.error(request, f"Unsupported file type '.{ext}'. Accepted: pdf, docx, txt, png.")
        return redirect(f"/?brand={brand.pk}")

    if uploaded.size > MAX_UPLOAD_BYTES:
        messages.error(request, "File exceeds the 20 MB size limit.")
        return redirect(f"/?brand={brand.pk}")

    if ext in MIME_MAGIC:
        header = uploaded.read(8)
        uploaded.seek(0)
        if not header.startswith(MIME_MAGIC[ext]):
            messages.error(request, f"File content does not match the '{ext}' format.")
            return redirect(f"/?brand={brand.pk}")

    try:
        extracted, was_truncated = extract_text(uploaded, ext)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(f"/?brand={brand.pk}")

    uploaded.seek(0)
    Document.objects.create(
        brand=brand,
        file=uploaded,
        filename=uploaded.name,
        file_type=ext,
        extracted_text=extracted,
        truncated=was_truncated,
    )

    msg = f"'{uploaded.name}' uploaded and text extracted."
    if was_truncated:
        msg += " Text was truncated at 12,000 characters."
    messages.success(request, msg)
    return redirect(f"/?brand={brand.pk}")


def _handle_delete(request, brand):
    """Delete a document by pk from POST data."""
    if brand is None:
        messages.error(request, "Brand not found.")
        return redirect("/")

    doc_id = request.POST.get("document_id")
    doc = get_object_or_404(Document, pk=doc_id, brand=brand)
    filename = doc.filename
    doc.delete()
    messages.success(request, f"'{filename}' deleted.")
    return redirect(f"/?brand={brand.pk}")


def _handle_extract(request, brand):
    """Trigger Claude signature extraction for the brand."""
    if brand is None:
        messages.error(request, "Brand not found.")
        return redirect("/")

    documents = list(brand.documents.all())
    if not documents:
        messages.error(request, "Upload at least one document before extracting a signature.")
        return redirect(f"/?brand={brand.pk}")

    previous_existed = brand.signature is not None
    texts = [doc.extracted_text for doc in documents]

    try:
        signature = extract_signature(texts)
    except ClaudeServiceError as exc:
        messages.error(request, f"Claude API error: {exc}")
        return redirect(f"/?brand={brand.pk}")

    brand.signature = signature
    brand.save(update_fields=["signature"])

    if previous_existed:
        messages.success(request, "Signature re-extracted and updated.")
    else:
        messages.success(request, "Tone-of-voice signature extracted successfully.")
    return redirect(f"/?brand={brand.pk}")


# ---------------------------------------------------------------------------
# Transform view  /transform/
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def transform_view(request):
    """Transform view — rewrite text in a brand's tone-of-voice.

    GET  — render transform form.
    POST — run transformation via Claude and display results.
    """
    brand_id = request.POST.get("brand_id") or request.GET.get("brand")
    brand = None
    if brand_id:
        brand = get_object_or_404(Brand, pk=brand_id)

    original = ""
    transformed = ""

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        if not text:
            messages.error(request, "Enter some text to transform.")
        elif brand is None:
            messages.error(request, "Select a brand first.")
        elif not brand.signature:
            messages.error(request, "No signature for this brand. Run extraction on the Upload page first.")
        else:
            try:
                original = text
                transformed = transform_text(text, brand.signature)
            except ClaudeServiceError as exc:
                messages.error(request, f"Claude API error: {exc}")

    return render(request, "transform.html", _ctx(
        request,
        brand=brand,
        original=original,
        transformed=transformed,
    ))
