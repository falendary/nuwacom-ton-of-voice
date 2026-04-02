from django.db import models


class Brand(models.Model):
    """A company whose tone-of-voice is being analyzed and applied."""

    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        help_text="Human context about the brand. Not used by Claude.",
    )
    signature = models.JSONField(
        null=True,
        blank=True,
        help_text="Extracted tone-of-voice signature with 5 characteristics.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    """A single uploaded file belonging to a Brand.

    Text is extracted from the file at upload time and stored in
    ``extracted_text``. Claude reads only this field — never the raw file.
    """

    FILE_TYPE_CHOICES = [
        ("pdf", "PDF"),
        ("docx", "Word Document"),
        ("txt", "Plain Text"),
        ("png", "PNG Image"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="uploads/")
    filename = models.CharField(max_length=255, help_text="Original filename for display.")
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    extracted_text = models.TextField(help_text="Plain text extracted from the file at upload time.")
    truncated = models.BooleanField(
        default=False,
        help_text="True if extracted_text was cut at 12,000 characters.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.filename
