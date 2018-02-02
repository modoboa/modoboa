# -*- coding: utf-8 -*-

"""Transport API urls."""

from __future__ import unicode_literals

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"relaydomains", viewsets.RelayDomainViewSet, base_name="relaydomain")
urlpatterns = router.urls
