"""Admin API urls."""

from rest_framework import routers

from . import api

router = routers.SimpleRouter()
router.register(r"domains", api.DomainViewSet, basename="domain")
router.register(
    r"domainaliases", api.DomainAliasViewSet, basename="domain_alias")
router.register(r"accounts", api.AccountViewSet, basename="account")
router.register(r"aliases", api.AliasViewSet, basename="alias")
router.register(
    r"senderaddresses", api.SenderAddressViewSet, basename="sender_address")

urlpatterns = router.urls
