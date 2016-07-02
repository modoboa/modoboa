"""Admin API urls."""

from rest_framework import routers

from . import api


router = routers.SimpleRouter()
router.register(r"domains", api.DomainViewSet, base_name="domain")
router.register(
    r"domainaliases", api.DomainAliasViewSet, base_name="domain_alias")
router.register(r"accounts", api.AccountViewSet, base_name="account")
router.register(r"aliases", api.AliasViewSet, base_name="alias")

urlpatterns = router.urls
