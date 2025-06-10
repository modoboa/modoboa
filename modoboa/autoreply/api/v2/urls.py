"""Autoreply API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"armessages", viewsets.ARMessageViewSet, basename="armessage")
router.register(
    r"account", viewsets.AccountARMessageViewSet, basename="account_armessage"
)
urlpatterns = router.urls
