"""Transport API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"relaydomains", viewsets.RelayDomainViewSet, basename="relaydomain")
urlpatterns = router.urls
