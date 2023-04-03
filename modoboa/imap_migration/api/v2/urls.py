"""API urls."""

from rest_framework import routers

from .viewsets import EmailProviderViewSet, MigrationViewSet


router = routers.SimpleRouter()
router.register(r"email-providers", EmailProviderViewSet)
router.register(r"migrations", MigrationViewSet)

urlpatterns = router.urls
