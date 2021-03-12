"""App related API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"statistics", viewsets.StatisticsViewSet, basename="statistics")

urlpatterns = router.urls
