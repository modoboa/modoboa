"""API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(r"email-providers", viewsets.EmailProviderViewSet)
router.register(r"migrations", viewsets.MigrationViewSet)

urlpatterns = router.urls
