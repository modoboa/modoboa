"""API urls."""

from rest_framework import routers

from ..v1 import viewsets as v1_viewsets
from .viewsets import EmailProviderViewSet


router = routers.SimpleRouter()
router.register(r"email-providers", EmailProviderViewSet)
router.register(r"migrations", v1_viewsets.MigrationViewSet)

urlpatterns = router.urls
