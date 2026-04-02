from django.contrib import admin

from core.models import Brand, Document


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    readonly_fields = ("filename", "file_type", "truncated", "uploaded_at")
    fields = ("filename", "file_type", "truncated", "uploaded_at")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "has_signature")
    readonly_fields = ("created_at",)
    inlines = [DocumentInline]

    @admin.display(boolean=True, description="Signature extracted")
    def has_signature(self, obj: Brand) -> bool:
        return obj.signature is not None


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "brand", "file_type", "truncated", "uploaded_at")
    list_filter = ("file_type", "truncated", "brand")
    readonly_fields = ("extracted_text", "truncated", "uploaded_at")
