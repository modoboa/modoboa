"""Webmail API urls."""

from rest_framework import routers

from modoboa.webmail import viewsets


router = routers.SimpleRouter()
router.register(r"mailboxes", viewsets.UserMailboxViewSet, basename="webmail-mailbox")
router.register(r"emails", viewsets.UserEmailViewSet, basename="webmail-email")

urlpatterns = router.urls
