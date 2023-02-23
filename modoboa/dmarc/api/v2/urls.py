"""App related API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"domains", viewsets.DMARCViewSet, basename="dmarc")

urlpatterns = router.urls
