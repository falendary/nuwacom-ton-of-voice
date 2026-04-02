from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Brand, Document
from core.services.claude import ClaudeServiceError

VALID_SIGNATURE = {
    "tone": "authoritative yet approachable",
    "sentence_rhythm": "short declaratives",
    "formality_level": "semi-formal",
    "forms_of_address": "you / your",
    "emotional_appeal": "rational-first",
}


def _txt_file(name: str = "sample.txt", content: bytes = b"Brand voice content.") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="text/plain")


def _make_document(brand: Brand, **kwargs) -> Document:
    defaults = {
        "file": "uploads/f.txt",
        "filename": "f.txt",
        "file_type": "txt",
        "extracted_text": "Brand text for extraction.",
        "truncated": False,
    }
    defaults.update(kwargs)
    return Document.objects.create(brand=brand, **defaults)


# ---------------------------------------------------------------------------
# Brand CRUD
# ---------------------------------------------------------------------------

class BrandCRUDTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_brands_returns_200(self) -> None:
        Brand.objects.create(name="Acme")
        response = self.client.get("/api/brands/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_create_brand_returns_201(self) -> None:
        response = self.client.post("/api/brands/", {"name": "Acme", "description": "Test brand"}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Acme")
        self.assertIsNone(data["signature"])
        self.assertIn("created_at", data)

    def test_retrieve_brand_returns_200(self) -> None:
        brand = Brand.objects.create(name="Acme")
        response = self.client.get(f"/api/brands/{brand.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Acme")

    def test_retrieve_unknown_brand_returns_404(self) -> None:
        response = self.client.get("/api/brands/9999/")
        self.assertEqual(response.status_code, 404)

    def test_partial_update_brand(self) -> None:
        brand = Brand.objects.create(name="Acme")
        response = self.client.patch(f"/api/brands/{brand.pk}/", {"description": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], "Updated")

    def test_delete_brand_returns_204(self) -> None:
        brand = Brand.objects.create(name="Acme")
        response = self.client.delete(f"/api/brands/{brand.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Brand.objects.filter(pk=brand.pk).exists())

    def test_delete_brand_cascades_to_documents(self) -> None:
        brand = Brand.objects.create(name="Acme")
        _make_document(brand)
        self.client.delete(f"/api/brands/{brand.pk}/")
        self.assertEqual(Document.objects.count(), 0)

    def test_signature_is_read_only(self) -> None:
        brand = Brand.objects.create(name="Acme")
        self.client.patch(f"/api/brands/{brand.pk}/", {"signature": {"tone": "fake"}}, format="json")
        brand.refresh_from_db()
        self.assertIsNone(brand.signature)

    def test_put_not_allowed(self) -> None:
        brand = Brand.objects.create(name="Acme")
        response = self.client.put(f"/api/brands/{brand.pk}/", {"name": "New"}, format="json")
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# Document upload / list / delete
# ---------------------------------------------------------------------------

class DocumentTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.brand = Brand.objects.create(name="Acme")
        self.list_url = f"/api/brands/{self.brand.pk}/documents/"

    def test_upload_txt_returns_201(self) -> None:
        response = self.client.post(self.list_url, {"file": _txt_file()}, format="multipart")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["filename"], "sample.txt")
        self.assertEqual(data["file_type"], "txt")
        self.assertFalse(data["truncated"])
        self.assertIn("Brand voice content", data["extracted_text"])

    def test_upload_sets_brand(self) -> None:
        response = self.client.post(self.list_url, {"file": _txt_file()}, format="multipart")
        self.assertEqual(response.json()["brand"], self.brand.pk)

    def test_upload_unsupported_type_returns_400(self) -> None:
        file = SimpleUploadedFile("data.xlsx", b"data", content_type="application/octet-stream")
        response = self.client.post(self.list_url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file type", response.json()["error"])

    @patch("core.api_views._validate_file", return_value=("txt", "File exceeds the 20 MB size limit."))
    def test_upload_oversized_file_returns_400(self, _mock) -> None:
        response = self.client.post(self.list_url, {"file": _txt_file()}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("20 MB", response.json()["error"])

    @patch("core.api_views.MAX_UPLOAD_BYTES", 0)
    def test_upload_oversized_via_actual_size_check_returns_400(self) -> None:
        response = self.client.post(self.list_url, {"file": _txt_file()}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("20 MB", response.json()["error"])

    def test_upload_wrong_magic_bytes_returns_400(self) -> None:
        fake_pdf = SimpleUploadedFile("doc.pdf", b"not a real pdf", content_type="application/pdf")
        response = self.client.post(self.list_url, {"file": fake_pdf}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not match", response.json()["error"])

    @patch("core.api_views.extract_text", side_effect=ValueError("unreadable file"))
    def test_upload_unreadable_file_returns_400(self, _mock) -> None:
        response = self.client.post(self.list_url, {"file": _txt_file()}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("unreadable file", response.json()["error"])

    def test_upload_no_file_returns_400(self) -> None:
        response = self.client.post(self.list_url, {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No file provided", response.json()["error"])

    def test_list_documents_returns_200(self) -> None:
        _make_document(self.brand)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_documents_unknown_brand_returns_404(self) -> None:
        response = self.client.get("/api/brands/9999/documents/")
        self.assertEqual(response.status_code, 404)

    def test_delete_document_returns_204(self) -> None:
        doc = _make_document(self.brand)
        response = self.client.delete(f"{self.list_url}{doc.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Document.objects.filter(pk=doc.pk).exists())

    def test_delete_document_wrong_brand_returns_404(self) -> None:
        other = Brand.objects.create(name="Other")
        doc = _make_document(other)
        response = self.client.delete(f"{self.list_url}{doc.pk}/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# /extract/ action
# ---------------------------------------------------------------------------

class ExtractActionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.brand = Brand.objects.create(name="Acme")
        self.url = f"/api/brands/{self.brand.pk}/extract/"

    def test_no_documents_returns_400(self) -> None:
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No documents", response.json()["error"])

    @patch("core.api_views.extract_signature", return_value=VALID_SIGNATURE)
    def test_success_response_shape(self, _mock) -> None:
        _make_document(self.brand)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["previous_signature_existed"])
        self.assertEqual(data["documents_analyzed"], 1)
        self.assertEqual(data["documents_truncated"], 0)
        self.assertEqual(data["signature"], VALID_SIGNATURE)
        self.assertEqual(data["brand_id"], self.brand.pk)

    @patch("core.api_views.extract_signature", return_value=VALID_SIGNATURE)
    def test_saves_signature_to_brand(self, _mock) -> None:
        _make_document(self.brand)
        self.client.post(self.url, {}, format="json")
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.signature, VALID_SIGNATURE)

    @patch("core.api_views.extract_signature", return_value=VALID_SIGNATURE)
    def test_previous_signature_existed_true_when_overwriting(self, _mock) -> None:
        self.brand.signature = {"tone": "old"}
        self.brand.save()
        _make_document(self.brand)
        response = self.client.post(self.url, {}, format="json")
        self.assertTrue(response.json()["previous_signature_existed"])

    @patch("core.api_views.extract_signature", return_value=VALID_SIGNATURE)
    def test_truncated_count_in_response(self, _mock) -> None:
        _make_document(self.brand, truncated=True)
        _make_document(self.brand, filename="f2.txt", truncated=False)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.json()["documents_truncated"], 1)
        self.assertEqual(response.json()["documents_analyzed"], 2)

    @patch("core.api_views.extract_signature", side_effect=ClaudeServiceError("upstream error"))
    def test_claude_failure_returns_502(self, _mock) -> None:
        _make_document(self.brand)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertIn("error", response.json())


# ---------------------------------------------------------------------------
# /transform/ action
# ---------------------------------------------------------------------------

class TransformActionTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.brand = Brand.objects.create(name="Acme", signature=VALID_SIGNATURE)
        self.url = f"/api/brands/{self.brand.pk}/transform/"

    def test_no_signature_returns_400(self) -> None:
        brand = Brand.objects.create(name="No-sig")
        response = self.client.post(f"/api/brands/{brand.pk}/transform/", {"text": "Hello"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No signature", response.json()["error"])

    def test_missing_text_returns_400(self) -> None:
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("text", response.json()["error"])

    def test_blank_text_returns_400(self) -> None:
        response = self.client.post(self.url, {"text": "   "}, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("core.api_views.transform_text", return_value="Transformed result.")
    def test_success_response_shape(self, _mock) -> None:
        response = self.client.post(self.url, {"text": "Original."}, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["original"], "Original.")
        self.assertEqual(data["transformed"], "Transformed result.")
        self.assertEqual(data["original_char_count"], len("Original."))
        self.assertEqual(data["transformed_char_count"], len("Transformed result."))
        self.assertEqual(data["signature_used"], VALID_SIGNATURE)
        self.assertEqual(data["brand_id"], self.brand.pk)

    @patch("core.api_views.transform_text", side_effect=ClaudeServiceError("upstream error"))
    def test_claude_failure_returns_502(self, _mock) -> None:
        response = self.client.post(self.url, {"text": "Hello"}, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertIn("error", response.json())
