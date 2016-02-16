"""Admin API urls."""

from rest_framework import routers

from . import api


router = routers.SimpleRouter()
router.register(r"domains", api.DomainViewSet, base_name="domain")
router.register(r"accounts", api.AccountViewSet, base_name="account")

urlpatterns = router.urls
