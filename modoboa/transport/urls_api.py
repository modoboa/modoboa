"""Transport API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(
    r"transports", viewsets.TransportViewSet, base_name="transport")
urlpatterns = router.urls
