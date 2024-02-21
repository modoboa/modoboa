"""App related urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(r"transports", viewsets.TransportViewSet, basename="transport")

urlpatterns = router.urls
