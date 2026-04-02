from rest_framework import serializers

from core.models import Brand, Document


class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer — signature is set by the server and is read-only from clients."""

    class Meta:
        model = Brand
        fields = ["id", "name", "description", "signature", "created_at"]
        read_only_fields = ["signature", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer — extracted_text, truncated, and metadata are set by the server."""

    class Meta:
        model = Document
        fields = ["id", "brand", "filename", "file_type", "extracted_text", "truncated", "uploaded_at"]
        read_only_fields = ["brand", "filename", "file_type", "extracted_text", "truncated", "uploaded_at"]
