from django.test import TestCase

from core.models import Brand, Document


class BrandModelTests(TestCase):
    def test_create_and_str(self) -> None:
        brand = Brand.objects.create(name="Acme")
        self.assertEqual(str(brand), "Acme")

    def test_signature_defaults_to_null(self) -> None:
        brand = Brand.objects.create(name="Acme")
        self.assertIsNone(brand.signature)

    def test_description_optional(self) -> None:
        brand = Brand.objects.create(name="Acme")
        self.assertEqual(brand.description, "")

    def test_created_at_set_automatically(self) -> None:
        brand = Brand.objects.create(name="Acme")
        self.assertIsNotNone(brand.created_at)


class DocumentModelTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="Acme")

    def _make_document(self, **kwargs) -> Document:
        defaults = {
            "brand": self.brand,
            "file": "uploads/sample.txt",
            "filename": "sample.txt",
            "file_type": "txt",
            "extracted_text": "Some extracted text.",
            "truncated": False,
        }
        defaults.update(kwargs)
        return Document.objects.create(**defaults)

    def test_create_and_str(self) -> None:
        doc = self._make_document()
        self.assertEqual(str(doc), "sample.txt")

    def test_truncated_defaults_to_false(self) -> None:
        doc = self._make_document()
        self.assertFalse(doc.truncated)

    def test_uploaded_at_set_automatically(self) -> None:
        doc = self._make_document()
        self.assertIsNotNone(doc.uploaded_at)

    def test_cascade_delete(self) -> None:
        self._make_document()
        self.assertEqual(Document.objects.count(), 1)
        self.brand.delete()
        self.assertEqual(Document.objects.count(), 0)
