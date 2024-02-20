"""App related API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"statistics", viewsets.StatisticsViewSet, basename="statistics")
router.register(r"logs/messages", viewsets.MaillogViewSet, basename="maillog")

urlpatterns = router.urls
