from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api_views import BrandViewSet, DocumentViewSet

router = DefaultRouter()
router.register("brands", BrandViewSet, basename="brand")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "brands/<int:brand_id>/documents/",
        DocumentViewSet.as_view({"get": "list", "post": "create"}),
        name="brand-documents-list",
    ),
    path(
        "brands/<int:brand_id>/documents/<int:pk>/",
        DocumentViewSet.as_view({"delete": "destroy"}),
        name="brand-documents-detail",
    ),
]
