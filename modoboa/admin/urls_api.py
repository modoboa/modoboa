"""Admin API urls."""

from rest_framework import routers

from . import api


router = routers.SimpleRouter()
router.register(r"domains", api.DomainViewSet, base_name="domain")

urlpatterns = router.urls
