from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import Brand, Document
from core.services.claude import ClaudeServiceError

VALID_SIGNATURE = {
    "tone": "authoritative yet approachable",
    "sentence_rhythm": "short declaratives",
    "formality_level": "semi-formal",
    "forms_of_address": "you / your",
    "emotional_appeal": "rational-first",
}


def _txt(name: str = "sample.txt", content: bytes = b"Brand voice content.") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="text/plain")


def _make_doc(brand: Brand, **kwargs) -> Document:
    defaults = {
        "file": "uploads/f.txt", "filename": "f.txt", "file_type": "txt",
        "extracted_text": "Brand text.", "truncated": False,
    }
    defaults.update(kwargs)
    return Document.objects.create(brand=brand, **defaults)


def _messages(response) -> list[str]:
    return [str(m) for m in response.context["messages"]]


# ---------------------------------------------------------------------------
# Upload view — GET
# ---------------------------------------------------------------------------

class UploadGetTests(TestCase):
    def test_renders_without_brand(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "upload.html")
        self.assertIsNone(response.context["brand"])

    def test_renders_with_brand(self) -> None:
        brand = Brand.objects.create(name="Acme")
        response = self.client.get(f"/?brand={brand.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["brand"], brand)

    def test_brands_list_in_context(self) -> None:
        Brand.objects.create(name="Acme")
        response = self.client.get("/")
        self.assertIn("brands", response.context)
        self.assertEqual(response.context["brands"].count(), 1)


# ---------------------------------------------------------------------------
# Upload view — file upload action
# ---------------------------------------------------------------------------

class UploadFileTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="Acme")

    def _post(self, **extra):
        return self.client.post("/", {
            "brand_id": self.brand.pk, "action": "upload", **extra,
        }, follow=True)

    def test_upload_txt_creates_document(self) -> None:
        self._post(file=_txt())
        self.assertEqual(Document.objects.count(), 1)

    def test_upload_success_message(self) -> None:
        response = self._post(file=_txt())
        self.assertTrue(any("uploaded" in m for m in _messages(response)))

    def test_upload_truncated_message(self) -> None:
        response = self._post(file=_txt(content=b"A" * 13_000))
        self.assertTrue(any("truncated" in m.lower() for m in _messages(response)))

    def test_upload_no_brand_redirects_home(self) -> None:
        response = self.client.post("/", {"action": "upload", "file": _txt()}, follow=True)
        self.assertRedirects(response, "/")

    def test_upload_no_file_shows_error(self) -> None:
        response = self._post()
        self.assertTrue(any("No file" in m for m in _messages(response)))

    def test_upload_unsupported_extension_shows_error(self) -> None:
        bad = SimpleUploadedFile("data.xlsx", b"data", content_type="application/octet-stream")
        response = self._post(file=bad)
        self.assertTrue(any("Unsupported" in m for m in _messages(response)))
        self.assertEqual(Document.objects.count(), 0)

    @patch("core.utils.MAX_UPLOAD_BYTES", 0)
    def test_upload_oversized_shows_error(self) -> None:
        response = self._post(file=_txt())
        self.assertTrue(any("20 MB" in m for m in _messages(response)))
        self.assertEqual(Document.objects.count(), 0)

    @patch("core.utils.MAX_FILENAME_LENGTH", 5)
    def test_upload_filename_too_long_shows_error(self) -> None:
        response = self._post(file=_txt())
        self.assertTrue(any("too long" in m.lower() for m in _messages(response)))
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_wrong_magic_bytes_shows_error(self) -> None:
        # .pdf extension but plaintext content — magic bytes check fails
        fake_pdf = SimpleUploadedFile("doc.pdf", b"not a real pdf", content_type="application/pdf")
        response = self._post(file=fake_pdf)
        self.assertTrue(any("does not match" in m for m in _messages(response)))
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_corrupt_txt_shows_error(self) -> None:
        # Bytes that cannot be decoded as UTF-8
        corrupt = SimpleUploadedFile("bad.txt", b"\xff\xfe\x00", content_type="text/plain")
        response = self._post(file=corrupt)
        self.assertTrue(any("error" in m.lower() or "read" in m.lower() for m in _messages(response)))


# ---------------------------------------------------------------------------
# Upload view — delete action
# ---------------------------------------------------------------------------

class UploadDeleteTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="Acme")

    def test_delete_removes_document(self) -> None:
        doc = _make_doc(self.brand)
        self.client.post("/", {
            "brand_id": self.brand.pk, "action": "delete", "document_id": doc.pk,
        })
        self.assertFalse(Document.objects.filter(pk=doc.pk).exists())

    def test_delete_success_message(self) -> None:
        doc = _make_doc(self.brand)
        response = self.client.post("/", {
            "brand_id": self.brand.pk, "action": "delete", "document_id": doc.pk,
        }, follow=True)
        self.assertTrue(any("deleted" in m.lower() for m in _messages(response)))

    def test_delete_no_brand_redirects_home(self) -> None:
        response = self.client.post("/", {"action": "delete", "document_id": 999}, follow=True)
        self.assertRedirects(response, "/")


# ---------------------------------------------------------------------------
# Upload view — extract action
# ---------------------------------------------------------------------------

class UploadExtractTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="Acme")
        _make_doc(self.brand)

    def _extract(self, brand=None) -> object:
        b = brand or self.brand
        return self.client.post("/", {
            "brand_id": b.pk, "action": "extract",
        }, follow=True)

    @patch("core.views.extract_signature", return_value=VALID_SIGNATURE)
    def test_extract_saves_signature(self, _mock) -> None:
        self._extract()
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.signature, VALID_SIGNATURE)

    @patch("core.views.extract_signature", return_value=VALID_SIGNATURE)
    def test_extract_new_signature_message(self, _mock) -> None:
        response = self._extract()
        self.assertTrue(any("extracted" in m.lower() for m in _messages(response)))

    @patch("core.views.extract_signature", return_value=VALID_SIGNATURE)
    def test_extract_overwrite_shows_updated_message(self, _mock) -> None:
        self.brand.signature = {"tone": "old"}
        self.brand.save()
        response = self._extract()
        self.assertTrue(any("updated" in m.lower() for m in _messages(response)))

    def test_extract_no_documents_shows_error(self) -> None:
        empty = Brand.objects.create(name="Empty")
        response = self._extract(brand=empty)
        self.assertTrue(any("Upload at least" in m for m in _messages(response)))

    @patch("core.views.extract_signature", side_effect=ClaudeServiceError("boom"))
    def test_extract_claude_failure_shows_error(self, _mock) -> None:
        response = self._extract()
        self.assertTrue(any("Claude API error" in m for m in _messages(response)))

    def test_extract_no_brand_redirects_home(self) -> None:
        response = self.client.post("/", {"action": "extract"}, follow=True)
        self.assertRedirects(response, "/")


# ---------------------------------------------------------------------------
# Transform view — GET
# ---------------------------------------------------------------------------

class TransformGetTests(TestCase):
    def test_renders(self) -> None:
        response = self.client.get("/transform/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transform.html")

    def test_renders_with_brand_param(self) -> None:
        brand = Brand.objects.create(name="Acme", signature=VALID_SIGNATURE)
        response = self.client.get(f"/transform/?brand={brand.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["brand"], brand)

    def test_original_and_transformed_empty_on_get(self) -> None:
        response = self.client.get("/transform/")
        self.assertEqual(response.context["original"], "")
        self.assertEqual(response.context["transformed"], "")


# ---------------------------------------------------------------------------
# Transform view — POST
# ---------------------------------------------------------------------------

class TransformPostTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="Acme", signature=VALID_SIGNATURE)

    def _post(self, **data):
        return self.client.post("/transform/", {"brand_id": self.brand.pk, **data})

    @patch("core.views.transform_text", return_value="Transformed output.")
    def test_success_shows_result(self, _mock) -> None:
        response = self._post(text="Hello.")
        self.assertEqual(response.context["original"], "Hello.")
        self.assertEqual(response.context["transformed"], "Transformed output.")

    @patch("core.views.transform_text", return_value="Transformed output.")
    def test_success_strips_whitespace(self, _mock) -> None:
        response = self._post(text="  Hello.  ")
        self.assertEqual(response.context["original"], "Hello.")

    def test_empty_text_shows_error(self) -> None:
        response = self._post(text="")
        self.assertTrue(any("Enter some text" in m for m in _messages(response)))
        self.assertEqual(response.context["transformed"], "")

    def test_blank_text_shows_error(self) -> None:
        response = self._post(text="   ")
        self.assertTrue(any("Enter some text" in m for m in _messages(response)))

    def test_no_brand_shows_error(self) -> None:
        response = self.client.post("/transform/", {"text": "Hello."})
        self.assertTrue(any("Select a brand" in m for m in _messages(response)))

    def test_no_signature_shows_error(self) -> None:
        no_sig = Brand.objects.create(name="No-sig")
        response = self.client.post("/transform/", {"brand_id": no_sig.pk, "text": "Hello."})
        self.assertTrue(any("No signature" in m for m in _messages(response)))

    @patch("core.views.transform_text", side_effect=ClaudeServiceError("API down"))
    def test_claude_failure_shows_error(self, _mock) -> None:
        response = self._post(text="Hello.")
        self.assertTrue(any("Claude API error" in m for m in _messages(response)))


# ---------------------------------------------------------------------------
# Admin — has_signature display method
# ---------------------------------------------------------------------------

class AdminHasSignatureTests(TestCase):
    def setUp(self) -> None:
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")

    def test_brand_changelist_renders(self) -> None:
        Brand.objects.create(name="With sig", signature=VALID_SIGNATURE)
        Brand.objects.create(name="No sig")
        response = self.client.get("/admin/core/brand/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "With sig")
        self.assertContains(response, "No sig")
