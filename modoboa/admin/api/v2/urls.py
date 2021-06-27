"""Admin API v2 urls."""

from rest_framework import routers

from modoboa.admin.api.v1 import viewsets as v1_viewsets

from . import viewsets

router = routers.SimpleRouter()
router.register(r"domains", viewsets.DomainViewSet, basename="domain")
router.register(
    r"domainaliases", v1_viewsets.DomainAliasViewSet, basename="domain_alias")
router.register(r"accounts", viewsets.AccountViewSet, basename="account")
router.register(r"aliases", viewsets.AliasViewSet, basename="alias")
router.register(
    r"senderaddresses", v1_viewsets.SenderAddressViewSet,
    basename="sender_address")
router.register(
    r"identities", viewsets.IdentityViewSet, basename="identities")

urlpatterns = router.urls
