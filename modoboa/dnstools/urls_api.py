"""App related API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"domains", viewsets.DNSViewSet, basename="dns")

urlpatterns = router.urls
