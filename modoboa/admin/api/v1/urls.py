"""Admin API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(r"domains", viewsets.DomainViewSet, basename="domain")
router.register(
    r"domainaliases", viewsets.DomainAliasViewSet, basename="domain_alias")
router.register(r"accounts", viewsets.AccountViewSet, basename="account")
router.register(r"aliases", viewsets.AliasViewSet, basename="alias")
router.register(
    r"senderaddresses", viewsets.SenderAddressViewSet, basename="sender_address")

urlpatterns = router.urls
