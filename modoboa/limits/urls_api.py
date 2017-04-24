"""Limits API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(
    r"resources", viewsets.ResourcesViewSet, base_name="resources")

urlpatterns = router.urls
