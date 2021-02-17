"""Core API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(r"account", viewsets.AccountViewSet, basename="account")
router.register(r"logs", viewsets.LogViewSet)

urlpatterns = router.urls
