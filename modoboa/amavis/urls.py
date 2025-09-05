"""Amavis urls."""

from rest_framework import routers

from modoboa.amavis import viewsets

router = routers.SimpleRouter()
router.register(r"quarantine", viewsets.QuarantineViewSet, basename="amavis-quarantine")
router.register(r"policies", viewsets.PolicyViewSet, basename="amavis-policy")

urlpatterns = router.urls
